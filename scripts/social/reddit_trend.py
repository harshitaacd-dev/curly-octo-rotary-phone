"""Measure the 2018-2024 trend in Reddit discussion of SEXUAL MORPHED / DEEPFAKE
images of women in Indian subreddits.

What it measures (and what it does not)
  Reddit has banned involuntary / faked sexual imagery since Feb 2018, so the
  images themselves are not on Reddit and are never collected here. What is
  measurable is TEXT: victims and families asking for help, news shared about
  cases, warnings, and solicitation. The trend in that text is a proxy for the
  problem, normalised by each subreddit's total activity so Reddit's own growth
  does not show up as an increase.

Method
  1. Recall: Arctic Shift full-text search of posts (title + body) and comments
     for RECALL_TERMS, per subreddit, in yearly windows (split automatically
     into halves when the archive times out).
  2. Precision: a hit counts as `sexual_morph` only if the same text has both
     a manipulation term (MANIP: morphed, deepfake, face swap, nudify, edited
     photo...) and a sexual term (SEXUAL: nude, obscene, porn, अश्लील, nangi...).
     `woman_ref` marks texts that also refer to a woman / girl.
     `offplatform` marks texts that also mention Telegram / WhatsApp / Discord /
     Signal / Snapchat / Instagram DMs (a count only; no links or channel names
     are extracted or stored in the summaries).
  3. Denominator: monthly total posts and comments per subreddit
     (Arctic Shift time_series).

Outputs
  data/social_raw/reddit/trend_hits_<years>.csv.gz      matched texts (git-ignored)
  data/social_summary/reddit_sexual_morph_monthly_<years>.csv  counts only
  data/social_summary/reddit_sexual_morph_yearly_<years>.csv   counts + rates per 100k
  data/social_raw/reddit/trend_coding_sample_<years>.csv  stratified sample for
      hand-coding hit type (victim/help-seeking, news, solicitation, other)

Usage
  python scripts/social/reddit_trend.py                       # defaults: 2018-2024
  python scripts/social/reddit_trend.py --no-comments         # posts only (much faster)
"""
import argparse
import gzip
import json
import re
import time

import pandas as pd

from common import OUT as RAW, REPO, get_json, new_session, pseudonym

ARCTIC = "https://arctic-shift.photon-reddit.com/api"
SUMMARY = REPO / "data" / "social_summary"

# Existed before 2018 -> balanced panel for the headline trend.
CORE = ["india", "IndiaSpeaks", "TwoXIndia", "AskIndia", "LegalAdviceIndia", "bangalore",
        "mumbai", "delhi", "Chennai", "hyderabad", "pune", "kolkata", "BollyBlindsNGossip"]
EXTENDED = ["unitedstatesofindia", "indiasocial"]  # created 2020

RECALL_TERMS = ["morphed", "morphing", "deepfake", "deepfakes", "nudify", "obscene",
                "sextortion", "undress", "faceswap", "nude"]

MANIP = re.compile(
    r"\bmorph\w*|deep\s*-?fakes?|face\s*-?swap\w*|nudif\w*|deep\s*nude|undress\w*|"
    r"photoshop\w*|\b(fake|edited|doctored|manipulated|ai[\s-]*generated|morphed)\s+"
    r"(nudes?|naked|photos?|pics?|pictures?|images?|videos?|clips?)\b|"
    r"\bedit(ed|ing)?\s+(her|my|their|his)\s+(photos?|pics?|pictures?|images?|dp)\b|"
    r"मॉर्फ|डीपफेक|एडिट", re.I)
SEXUAL = re.compile(
    r"\bnudes?\b|\bnud(e|ity)\w*|naked|\bporn\w*|obscene|\bsexual\w*|explicit|vulgar|lewd|"
    r"\bxxx\b|\bnsfw\b|sextort\w*|indecent|objectionable|semi[\s-]*nude|undress\w*|nudif\w*|"
    r"\bnangi\b|ashleel|अश्लील|न्यूड|नग्न|गंदी", re.I)
OFFPLATFORM = re.compile(
    r"telegram|\btg\b|\btele\s*gram|whats\s*app|\bwa\s*group|discord|\bsignal\b|snap\s*chat|"
    r"insta(gram)?\s*(dm|group|page)|\bdm\b|टेलीग्राम|व्हाट्सएप", re.I)

WOMAN = re.compile(
    r"\b(woman|women|girls?|she|her|wife|sister|girlfriend|gf|daughter|mother|actress\w*|"
    r"female|lady|ladies|ladki\w*|aurat|bhabhi|niece|cousin sister|classmate)\b|महिला|लड़की|बेटी", re.I)


def search(s, kind, sub, term, lo, hi, depth=0):
    """All hits for one (kind, sub, term) in [lo, hi); halves the window on timeout."""
    out, cursor = [], lo
    field = "query" if kind == "posts" else "body"
    fields = ("id,created_utc,subreddit,title,selftext,author,score,num_comments"
              if kind == "posts" else "id,created_utc,subreddit,body,author,score,link_id")
    while True:
        p = {"subreddit": sub, field: term, "limit": 100, "sort": "asc",
             "after": cursor, "before": hi, "fields": fields}
        try:
            data = get_json(s, f"{ARCTIC}/{kind}/search", p, tries=4, wait=3).get("data") or []
        except RuntimeError:
            if hi - lo > 15 * 86400 and depth < 6:
                mid = (lo + hi) // 2
                return out + search(s, kind, sub, term, cursor, mid, depth + 1) + \
                    search(s, kind, sub, term, mid, hi, depth + 1)
            print(f"    gave up: {kind} r/{sub} '{term}' {lo}-{hi}")
            return out
        out += data
        time.sleep(1.5)
        if len(data) < 100:
            return out
        cursor = int(data[-1]["created_utc"]) + 1


def series(s, sub, kind, after, before):
    j = get_json(s, f"{ARCTIC}/time_series",
                 {"key": f"r/{sub}/{kind}/count", "precision": "month",
                  "after": after, "before": before}, tries=4, wait=3)
    time.sleep(1.5)
    return {pd.Timestamp(d["date"], unit="s").strftime("%Y-%m"): d["value"] for d in j.get("data") or []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subreddits", nargs="+", default=CORE + EXTENDED)
    ap.add_argument("--terms", nargs="+", default=RECALL_TERMS)
    ap.add_argument("--from", dest="after", default="2018-01-01")
    ap.add_argument("--to", dest="before", default="2025-01-01", help="exclusive")
    ap.add_argument("--no-comments", action="store_true")
    a = ap.parse_args()
    lo, hi = int(pd.Timestamp(a.after, tz="UTC").timestamp()), int(pd.Timestamp(a.before, tz="UTC").timestamp())
    tag = f"{a.after[:4]}_{int(a.before[:4]) - 1}"
    kinds = ["posts"] if a.no_comments else ["posts", "comments"]
    s = new_session()

    hits = []
    for sub in a.subreddits:
        for kind in kinds:
            n0 = len(hits)
            for term in a.terms:
                for y in range(int(a.after[:4]), int(a.before[:4])):
                    ylo = max(lo, int(pd.Timestamp(f"{y}-01-01", tz="UTC").timestamp()))
                    yhi = min(hi, int(pd.Timestamp(f"{y + 1}-01-01", tz="UTC").timestamp()))
                    # Resumable: each (kind, sub, term, year) result is cached in the git-ignored raw folder.
                    cache = RAW / "reddit" / "trend_cache" / f"{kind}_{sub}_{term}_{y}.json.gz"
                    if cache.exists():
                        found = json.load(gzip.open(cache, "rt"))
                    else:
                        found = search(s, kind, sub, term, ylo, yhi)
                        for r in found:  # never cache raw usernames
                            r["author"] = pseudonym(r.get("author"))
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        json.dump(found, gzip.open(cache, "wt"))
                    for r in found:
                        text = (r.get("title", "") + "\n" + (r.get("selftext") or "")
                                if kind == "posts" else r.get("body") or "")
                        hits.append({"kind": kind[:-1], "id": r["id"], "subreddit": r["subreddit"],
                                     "created_utc": r["created_utc"], "term": term, "text": text,
                                     "author_hash": pseudonym(r.get("author")), "score": r.get("score"),
                                     "url": (f"https://www.reddit.com/r/{r['subreddit']}/comments/{r['id']}/"
                                             if kind == "posts" else
                                             f"https://www.reddit.com/r/{r['subreddit']}/comments/"
                                             f"{(r.get('link_id') or 't3_')[3:]}/_/{r['id']}/")})
            print(f"  r/{sub} {kind}: {len(hits) - n0} raw hits")

    h = pd.DataFrame(hits)
    h["term"] = h.groupby(["kind", "id"]).term.transform(lambda x: ";".join(sorted(set(x))))
    h = h.drop_duplicates(["kind", "id"])
    h = h[~h.text.str.strip().isin(["", "[deleted]", "[removed]", "\n[deleted]", "\n[removed]"])]
    h["month"] = pd.to_datetime(h.created_utc, unit="s").dt.strftime("%Y-%m")
    h["year"] = h.month.str[:4]
    h["manip"] = h.text.str.contains(MANIP).astype(int)
    h["sexual"] = h.text.str.contains(SEXUAL).astype(int)
    h["sexual_morph"] = h.manip & h.sexual
    h["woman_ref"] = h.text.str.contains(WOMAN).astype(int)
    h["offplatform"] = h.text.str.contains(OFFPLATFORM).astype(int)
    h["panel"] = h.subreddit.map(lambda x: "core" if x in CORE else "extended")

    (RAW / "reddit").mkdir(parents=True, exist_ok=True)
    h.to_csv(RAW / "reddit" / f"trend_hits_{tag}.csv.gz", index=False, compression="gzip")

    # Denominators
    den = []
    for sub in a.subreddits:
        for kind in kinds:
            for m, v in series(s, sub, kind, a.after, a.before).items():
                den.append({"subreddit": sub, "kind": kind[:-1], "month": m, "total": v})
    den = pd.DataFrame(den)

    h["woman_offplatform"] = h.woman_ref & h.offplatform
    sm = h[h.sexual_morph == 1]
    cnt = sm.groupby(["subreddit", "kind", "month"]).agg(
        sexual_morph=("id", "size"), sexual_morph_woman=("woman_ref", "sum"),
        sexual_morph_offplatform=("offplatform", "sum"),
        sexual_morph_woman_offplatform=("woman_offplatform", "sum")).reset_index()
    monthly = den.merge(cnt, on=["subreddit", "kind", "month"], how="left").fillna(
        {"sexual_morph": 0, "sexual_morph_woman": 0, "sexual_morph_offplatform": 0,
         "sexual_morph_woman_offplatform": 0})
    monthly["panel"] = monthly.subreddit.map(lambda x: "core" if x in CORE else "extended")
    monthly = monthly[(monthly.month >= a.after[:7]) & (monthly.month < a.before[:7])]
    SUMMARY.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(SUMMARY / f"reddit_sexual_morph_monthly_{tag}.csv", index=False)

    monthly["year"] = monthly.month.str[:4]
    COUNTS = ["sexual_morph", "sexual_morph_woman", "sexual_morph_offplatform", "sexual_morph_woman_offplatform"]
    yearly = monthly.groupby(["panel", "kind", "year"])[["total"] + COUNTS].sum().reset_index()
    for c in COUNTS:
        yearly[f"{c}_per_100k"] = (yearly[c] / yearly.total * 1e5).round(2)
    yearly.to_csv(SUMMARY / f"reddit_sexual_morph_yearly_{tag}.csv", index=False)

    # Stratified sample for hand-coding (up to 30 per year, woman_ref first)
    samp = (sm.sort_values("woman_ref", ascending=False).groupby("year").head(30)
            .assign(code_type="", code_sexual_morph_confirmed="", code_target_woman="")
            [["kind", "id", "subreddit", "month", "url", "text", "woman_ref",
              "code_type", "code_sexual_morph_confirmed", "code_target_woman"]])
    samp.to_csv(RAW / "reddit" / f"trend_coding_sample_{tag}.csv", index=False)

    print(f"\nraw hits {len(h)}; sexual_morph {len(sm)} ({sm.woman_ref.sum()} with woman_ref)")
    print(yearly.to_string(index=False))


if __name__ == "__main__":
    main()
