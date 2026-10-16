"""Build a seed list of YouTube videos that Indian fact-checkers identified as
deepfakes / AI-generated / manipulated media presented as real.

Sources
  wp      (default, no key) WordPress REST search of Indian IFCN-style
          fact-checkers that expose it: Alt News, Factly, Newschecker,
          Fact Crescendo, DFRAC. Article HTML comes back in the API response,
          so no article pages are scraped.
  google  Google Fact Check Tools API (ClaimReview). Needs a key with the
          "Fact Check Tools API" enabled: FACTCHECK_API_KEY, or YOUTUBE_API_KEY
          if the same Google Cloud project has both APIs enabled.

For each fact-check the YouTube links in the article (watch, youtu.be, shorts,
embed, live) are extracted; links that appear in many articles (the
fact-checker's own channel / promo videos) are dropped. Each video is then
checked with YouTube's public oEmbed endpoint (no key): available videos
return their title and channel, removed / private ones return an error.

Videos are never downloaded.

Outputs (data/deepfakes/):
  factchecks_<from>_<to>.csv            one row per fact-check article
  factcheck_youtube_seeds_<from>_<to>.csv one row per (article, YouTube video)

Usage:
  python scripts/social/factcheck_deepfakes.py --from 2018-01-01 --to 2024-12-31
  python scripts/social/factcheck_deepfakes.py --sources wp google
  then: python scripts/social/youtube_comments.py --queries \
          --seed-file data/deepfakes/factcheck_youtube_seeds_2018_2024.csv
"""
import argparse
import html
import os
import re
import time
from collections import Counter

import pandas as pd

from common import REPO, get_json, new_session

OUT = REPO / "data" / "deepfakes"

WP_SITES = {
    "Alt News": "https://www.altnews.in",
    "Factly": "https://factly.in",
    "Newschecker": "https://newschecker.in",
    "Fact Crescendo": "https://www.factcrescendo.com",
    "DFRAC": "https://dfrac.org",
}

TERMS = ["deepfake", "deep fake", "AI-generated", "AI generated", "artificial intelligence",
         "voice clone", "cloned voice", "AI voice", "face swap", "morphed video",
         "digitally altered", "synthetic", "डीपफेक", "एआई"]

# Classify what the fact-check says the media is (from the article title + lede).
KIND = [
    ("deepfake/face-swap", r"deep\s*-?fake|face[\s-]*swap|डीपफेक"),
    ("ai-voice", r"voice\s*clon|cloned\s*voice|ai[\s-]*(generated\s*)?(voice|audio)"),
    ("ai-generated", r"\bai\b|a\.i\.|artificial intelligence|ai-generated|generated|एआई|synthetic"),
    ("edited/morphed", r"morph|edit|doctor|altered|manipulat|clipped|cropped|spliced"),
]
WOMAN = re.compile(r"\b(woman|women|girl|girls|actress|female|she|her|lady|mla|mp)\b|"
                   r"महिला|लड़की|अभिनेत्री", re.I)

YT_RE = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:[^\"'\s<>]*&)?v=|embed/|shorts/|live/|v/)"
    r"|youtu\.be/)([A-Za-z0-9_-]{11})")


def text_of(h):
    return html.unescape(re.sub(r"<[^>]+>", " ", h or "")).strip()


def classify(s):
    s = s.lower()
    return next((k for k, pat in KIND if re.search(pat, s)), "other")


def wp_search(s, name, base, terms, after, before):
    rows = []
    for term in terms:
        page = 1
        while True:
            p = {"search": term, "after": f"{after}T00:00:00", "before": f"{before}T23:59:59",
                 "per_page": 100, "page": page, "_fields": "id,date,link,title,excerpt,content"}
            r = s.get(f"{base}/wp-json/wp/v2/posts", params=p, timeout=120)
            if r.status_code == 400:  # page past the end
                break
            if r.status_code != 200:
                print(f"  {name} '{term}': HTTP {r.status_code}")
                break
            posts = r.json()
            for post in posts:
                rows.append({
                    "publisher": name, "post_id": post["id"], "date": post["date"][:10],
                    "url": post["link"], "title": text_of(post["title"]["rendered"]),
                    "excerpt": text_of(post["excerpt"]["rendered"])[:400],
                    "content_html": post["content"]["rendered"], "matched_term": term,
                    "verdict": "",
                })
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                break
            page += 1
            time.sleep(1)
        time.sleep(1)
    print(f"  {name}: {len({r['post_id'] for r in rows})} articles")
    return rows


def google_search(s, key, terms, after, before):
    rows = []
    for term in terms:
        token = None
        while True:
            p = {"query": term, "key": key, "pageSize": 100, "languageCode": "en"}
            if token:
                p["pageToken"] = token
            res = get_json(s, "https://factchecktools.googleapis.com/v1alpha1/claims:search", p)
            for c in res.get("claims", []):
                for rv in c.get("claimReview", []):
                    d = (rv.get("reviewDate") or c.get("claimDate") or "")[:10]
                    if not d or not after <= d <= before:
                        continue
                    rows.append({
                        "publisher": rv.get("publisher", {}).get("name", ""), "post_id": "",
                        "date": d, "url": rv.get("url"), "title": rv.get("title") or c.get("text", ""),
                        "excerpt": c.get("text", "")[:400], "content_html": "",
                        "matched_term": f"google:{term}", "verdict": rv.get("textualRating", ""),
                    })
            token = res.get("nextPageToken")
            if not token:
                break
            time.sleep(0.5)
    print(f"  Google Fact Check API: {len(rows)} reviews")
    return rows


def fetch_article(s, url):
    """Only used for Google results, whose API response has no article body."""
    try:
        r = s.get(url, timeout=60)
        return r.text if r.ok else ""
    except Exception:
        return ""


def oembed(s, vid):
    r = s.get("https://www.youtube.com/oembed",
              params={"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"}, timeout=60)
    if r.status_code == 200:
        j = r.json()
        return "available", j.get("title", ""), j.get("author_name", ""), j.get("author_url", "")
    return {401: "private/embedding-off", 403: "private/embedding-off",
            404: "removed/unavailable", 400: "removed/unavailable"}.get(r.status_code,
                                                                        f"http_{r.status_code}"), "", "", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="after", default="2018-01-01")
    ap.add_argument("--to", dest="before", default="2024-12-31")
    ap.add_argument("--sources", nargs="+", default=["wp"], choices=["wp", "google"])
    ap.add_argument("--terms", nargs="+", default=TERMS)
    ap.add_argument("--boilerplate-min", type=int, default=5,
                    help="drop video IDs linked from at least this many articles of one publisher")
    ap.add_argument("--no-oembed", action="store_true")
    ap.add_argument("--include-other", action="store_true",
                    help="also seed videos from fact-checks whose title/lede has no AI/deepfake/"
                         "manipulation wording (mostly articles that merely mention AI)")
    a = ap.parse_args()

    s = new_session("Mozilla/5.0 (research; deepfake fact-check seed list)")
    rows = []
    if "wp" in a.sources:
        for name, base in WP_SITES.items():
            rows += wp_search(s, name, base, a.terms, a.after, a.before)
    if "google" in a.sources:
        key = os.environ.get("FACTCHECK_API_KEY") or os.environ.get("YOUTUBE_API_KEY")
        if not key:
            ap.error("google source needs FACTCHECK_API_KEY or YOUTUBE_API_KEY")
        g = google_search(s, key, a.terms, a.after, a.before)
        for r in g:
            r["content_html"] = fetch_article(s, r["url"])
            time.sleep(1)
        rows += g

    df = pd.DataFrame(rows)
    if df.empty:
        print("no fact-checks found")
        return
    df["matched_term"] = df.groupby("url").matched_term.transform(lambda x: "; ".join(sorted(set(x))))
    df = df.drop_duplicates("url").reset_index(drop=True)
    df["kind"] = (df.title + " " + df.excerpt).map(classify)
    df["mentions_woman"] = (df.title + " " + df.excerpt).str.contains(WOMAN).astype(int)
    df["youtube_ids"] = df.content_html.fillna("").map(lambda h: sorted(set(YT_RE.findall(h))))

    # Drop each publisher's boilerplate videos (own channel promos embedded in every article).
    per_pub = Counter((p, v) for p, ids in zip(df.publisher, df.youtube_ids) for v in ids)
    boiler = {k for k, n in per_pub.items() if n >= a.boilerplate_min}
    df["youtube_ids"] = [[v for v in ids if (p, v) not in boiler]
                         for p, ids in zip(df.publisher, df.youtube_ids)]
    df["n_youtube"] = df.youtube_ids.map(len)
    df["year"] = df.date.str[:4]

    OUT.mkdir(parents=True, exist_ok=True)
    tag = f"{a.after[:4]}_{a.before[:4]}"
    arts = df.drop(columns=["content_html"]).assign(youtube_ids=df.youtube_ids.map(" ".join))
    arts.sort_values("date").to_csv(OUT / f"factchecks_{tag}.csv", index=False)

    seeds = df[(df.n_youtube > 0) & (a.include_other | df.kind.ne("other"))].explode("youtube_ids").rename(columns={"youtube_ids": "video_id"})
    seeds = seeds[["video_id", "publisher", "date", "year", "url", "title", "kind",
                   "mentions_woman", "verdict"]].rename(
        columns={"date": "factcheck_date", "url": "factcheck_url", "title": "factcheck_title"})
    if not a.no_oembed and len(seeds):
        status = {}
        for vid in seeds.video_id.unique():
            status[vid] = oembed(s, vid)
            time.sleep(0.5)
        seeds[["yt_status", "yt_title", "yt_channel", "yt_channel_url"]] = \
            pd.DataFrame([status[v] for v in seeds.video_id], index=seeds.index)
    seeds.sort_values("factcheck_date").to_csv(OUT / f"factcheck_youtube_seeds_{tag}.csv", index=False)

    print(f"\n{len(df)} fact-checks, {df.n_youtube.gt(0).sum()} with YouTube links, "
          f"{seeds.video_id.nunique()} unique videos")
    print(pd.crosstab(df.year, df.kind, margins=True).to_string())
    if "yt_status" in seeds:
        print(seeds.drop_duplicates("video_id").yt_status.value_counts().to_string())


if __name__ == "__main__":
    main()
