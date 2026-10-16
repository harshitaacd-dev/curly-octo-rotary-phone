"""Discover India-based YouTube channels posting AI-generated content, and
candidate deepfake videos, year by year (default 2018-2024).

Modes
  ai-channels  searches AI-content queries; output = channels with evidence
  deepfakes    searches deepfake / "fake video" queries; output = candidate
               videos with evidence (plus their channels)

Evidence recorded for each video (nothing is downloaded, metadata only):
  self_labelled    YouTube's status.containsSyntheticMedia flag (creator
                   disclosure); blank if the API does not return it
  ai_cue           AI-tool / AI-content wording in title, description or tags
  debunk_comments  with --comments N: how many of the first N comments say
                   it is fake / AI / edited ("fake hai", "AI hai", ...)
Channel evidence: declared country (snippet.country), and with
--profile-channels the share of the channel's last 50 uploads with ai_cue.

Quota (10,000 units/day by default): each search page = 100 units, so
queries x years x pages searches; videos/channels lookups = 1 unit per 50;
comments = 1 unit per page of 100. Example: 10 queries x 7 years x 1 page =
7,000 units -> run one mode per day, or pass fewer --years / --queries.

Usage:
  python scripts/social/youtube_discover.py --mode ai-channels --profile-channels 100
  python scripts/social/youtube_discover.py --mode deepfakes --comments 100
"""
import argparse
import os
import re
import sys
import time

import pandas as pd

from common import REPO, load_targets, new_session
from youtube_comments import UNITS, QuotaExceeded, call

OUT = REPO / "data" / "deepfakes"

# Tool names that are also ordinary words ("audio", Hindi "suno" = listen, "runway") need
# word boundaries or a qualifier; "#ai..." hashtags are limited to AI stems so #airpods,
# #aids, #aishwarya... don't match.
AI_CUE = re.compile(
    r"\bai\b|a\.i\.|artificial intelligence|ai[\s-]*generated|generativ|deep\s*-?fake|"
    r"#ai(?:\b|_|art|cover|gen|vide|voice|tool|anim|song|sing|music|imag|photo|model|influencer|"
    r"avatar|filter|girl|story|creat|edit|prompt|short|track|visual|wallpaper|upscal|trailer|"
    r"technolog|news|tutorial|tip|trick|in[a-z]|for|use|script|journey|enhanc|recreat|colori|human|"
    r"fake|orreal|orhuman|mosaic|dynamic|research|lien|c\b|faceswap|viral)\w*|"
    r"face\s*-?swap|voice\s*clon|midjourney|stable\s*diffusion|\bdall[\s-]*e\b|"
    r"runway\s*(?:ml|gen|ai)|pika\s*labs|\bsora\b|\bveo\s*\d?\b|\bkling\b|hailuo|luma\s*(?:ai|dream)|"
    r"elevenlabs|\bsuno\s*ai\b|\budio\b|heygen|synthesia|एआई|डीपफेक|कृत्रिम बुद्धि", re.I)
DEBUNK = re.compile(
    r"\bfake\s*(hai|h|he|video|news)?\b|\bai\s*(hai|h|se|ka|generated|video)\b|deep\s*-?fake|"
    r"edit(ed)?\s*(hai|h|video)?|asli\s*nahi|nakli|morph|फर्जी|नकली|एडिट", re.I)


def year_windows(years):
    for y in years:
        yield y, f"{y}-01-01T00:00:00Z", f"{y + 1}-01-01T00:00:00Z"


def search(s, q, after, before, pages, region, lang):
    out, token = [], None
    for _ in range(pages):
        p = {"part": "snippet", "q": q, "type": "video", "maxResults": 50, "order": "relevance",
             "regionCode": region, "relevanceLanguage": lang,
             "publishedAfter": after, "publishedBefore": before}
        if token:
            p["pageToken"] = token
        res = call(s, "search", **p)
        out += [i["id"]["videoId"] for i in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break
    return out


def videos(s, ids):
    rows = []
    for i in range(0, len(ids), 50):
        res = call(s, "videos", part="snippet,status,statistics", id=",".join(ids[i:i + 50]))
        for v in res.get("items", []):
            sn, st, stat = v["snippet"], v.get("status", {}), v.get("statistics", {})
            blob = " ".join([sn.get("title", ""), sn.get("description", "")[:2000],
                             " ".join(sn.get("tags", []))])
            rows.append({
                "video_id": v["id"], "published_at": sn.get("publishedAt"),
                "year": (sn.get("publishedAt") or "")[:4], "title": sn.get("title"),
                "channel_id": sn.get("channelId"), "channel_title": sn.get("channelTitle"),
                "language": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "",
                "views": stat.get("viewCount"), "comments": stat.get("commentCount"),
                "self_labelled": st.get("containsSyntheticMedia", ""),
                "ai_cue": int(bool(AI_CUE.search(blob))),
                "ai_cue_terms": "; ".join(sorted({m.group(0).lower() for m in AI_CUE.finditer(blob)}))[:200],
            })
    return pd.DataFrame(rows)


def channels(s, ids):
    rows = []
    for i in range(0, len(ids), 50):
        res = call(s, "channels", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
        for c in res.get("items", []):
            rows.append({
                "channel_id": c["id"], "channel_title": c["snippet"].get("title"),
                "country": c["snippet"].get("country", ""),
                "channel_created": (c["snippet"].get("publishedAt") or "")[:10],
                "subscribers": c.get("statistics", {}).get("subscriberCount"),
                "channel_videos": c.get("statistics", {}).get("videoCount"),
                "uploads_playlist": c.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads"),
            })
    return pd.DataFrame(rows)


def ai_share(s, playlist):
    """Share of the last 50 uploads whose title/description has an AI cue."""
    try:
        res = call(s, "playlistItems", part="snippet", playlistId=playlist, maxResults=50)
    except QuotaExceeded:
        raise
    except Exception:
        return None, 0
    items = res.get("items", [])
    hits = sum(bool(AI_CUE.search(i["snippet"].get("title", "") + " " +
                                  i["snippet"].get("description", "")[:1000])) for i in items)
    return (round(hits / len(items), 3) if items else None), len(items)


def debunk_count(s, vid, n):
    try:
        res = call(s, "commentThreads", part="snippet", videoId=vid, maxResults=min(n, 100),
                   textFormat="plainText", order="relevance")
    except QuotaExceeded:
        raise
    except Exception:
        return None, 0
    texts = [i["snippet"]["topLevelComment"]["snippet"].get("textOriginal", "")
             for i in res.get("items", [])]
    return sum(bool(DEBUNK.search(t)) for t in texts), len(texts)


def main():
    t = load_targets()["youtube"]
    d = t["discovery"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["ai-channels", "deepfakes"], required=True)
    ap.add_argument("--queries", nargs="+")
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2018, 2025)))
    ap.add_argument("--pages", type=int, default=1, help="search pages (50 videos) per query-year")
    ap.add_argument("--comments", type=int, default=0, help="deepfakes: scan this many comments per video")
    ap.add_argument("--profile-channels", type=int, default=0,
                    help="profile the last 50 uploads of this many top candidate channels")
    a = ap.parse_args()
    if "YOUTUBE_API_KEY" not in os.environ:
        ap.error("set YOUTUBE_API_KEY")
    queries = a.queries or d["ai_content_queries" if a.mode == "ai-channels" else "deepfake_queries"]

    s = new_session()
    tag = f"{a.mode}_{min(a.years)}_{max(a.years)}"
    hits, done = [], []
    try:
        for q in queries:
            for y, lo, hi in year_windows(a.years):
                ids = search(s, q, lo, hi, a.pages, t["region_code"], t["relevance_language"])
                hits += [(v, q, y) for v in ids]
                done.append((q, y))
                print(f"  {q!r} {y}: {len(ids)}")
                time.sleep(0.2)
        found = pd.DataFrame(hits, columns=["video_id", "query", "search_year"])
        found = found.groupby("video_id").agg(queries=("query", lambda x: "; ".join(sorted(set(x))))).reset_index()
        vids = videos(s, found.video_id.tolist()).merge(found, on="video_id")
        ch = channels(s, vids.channel_id.dropna().unique().tolist())
    except QuotaExceeded as e:
        OUT.mkdir(parents=True, exist_ok=True)
        part = OUT / f"youtube_{tag}_partial_search_hits.csv"
        pd.DataFrame(hits, columns=["video_id", "query", "search_year"]).to_csv(part, index=False)
        left = [(q, y) for q in queries for y in a.years if (q, y) not in done]
        print(f"QUOTA EXCEEDED on {e} after ~{UNITS['used']} units: {len(hits)} search hits -> {part}; "
              f"{len(left)} query-years not searched: {left}")
        sys.exit(3)
    vids = vids.merge(ch[["channel_id", "country", "subscribers"]], on="channel_id", how="left")
    vids["country"] = vids.country.fillna("")

    if a.mode == "deepfakes" and a.comments:
        res = []
        try:
            for v in vids.video_id:
                res.append(debunk_count(s, v, a.comments))
        except QuotaExceeded:
            print(f"QUOTA EXCEEDED: debunk comments scanned for {len(res)} of {len(vids)} videos")
            res += [(None, 0)] * (len(vids) - len(res))
        vids["debunk_comments"] = [r[0] for r in res]
        vids["comments_scanned"] = [r[1] for r in res]

    agg = vids.groupby("channel_id").agg(
        n_videos_found=("video_id", "size"), n_ai_cue=("ai_cue", "sum"),
        n_self_labelled=("self_labelled", lambda x: int((x == True).sum())),  # noqa: E712
        first_video=("published_at", "min"), last_video=("published_at", "max"),
        years=("year", lambda x: ",".join(sorted(set(x)))),
        queries=("queries", lambda x: "; ".join(sorted(set("; ".join(x).split("; "))))[:300]),
    ).reset_index().merge(ch.drop(columns=["uploads_playlist"]), on="channel_id", how="left")
    agg["country"] = agg.country.fillna("")
    agg["in_india"] = agg.country.eq("IN").astype(int)
    agg = agg.sort_values(["in_india", "n_ai_cue", "n_videos_found"], ascending=False)

    if a.profile_channels:
        pl = ch.set_index("channel_id").uploads_playlist
        top = agg[(agg.n_ai_cue > 0) & agg.country.isin(["IN", ""])].head(a.profile_channels)
        shares = {}
        try:
            for c in top.channel_id:
                if pl.get(c):
                    shares[c] = ai_share(s, pl.get(c))
        except QuotaExceeded:
            print(f"QUOTA EXCEEDED: profiled {len(shares)} of {len(top)} channels")
        agg["recent_ai_share"] = agg.channel_id.map(lambda c: shares.get(c, (None, 0))[0])
        agg["recent_uploads_checked"] = agg.channel_id.map(lambda c: shares.get(c, (None, 0))[1])

    def evidence(r):
        e = []
        if r.n_self_labelled:
            e.append(f"self-labelled x{r.n_self_labelled}")
        if r.n_ai_cue:
            e.append(f"AI wording x{r.n_ai_cue}")
        if pd.notna(r.get("recent_ai_share")):
            e.append(f"{r.recent_ai_share:.0%} of recent uploads AI-worded")
        e.append("country=IN" if r.in_india else f"country={r.country or 'not set'}")
        return "; ".join(e)
    agg["evidence"] = agg.apply(evidence, axis=1)
    agg["manually_verified"] = ""  # fill in by hand

    OUT.mkdir(parents=True, exist_ok=True)
    vids.sort_values("published_at").to_csv(OUT / f"youtube_{tag}_videos.csv", index=False)
    agg.to_csv(OUT / f"youtube_{tag}_channels.csv", index=False)
    print(f"{len(vids)} videos, {len(agg)} channels ({agg.in_india.sum()} declare India) -> "
          f"data/deepfakes/youtube_{tag}_*.csv")
    print(vids.groupby("year").agg(videos=("video_id", "size"), ai_cue=("ai_cue", "sum")).to_string())
    print("self_labelled field returned:", vids.self_labelled.ne("").any())
    print(f"~{UNITS['used']} quota units used")


if __name__ == "__main__":
    main()
