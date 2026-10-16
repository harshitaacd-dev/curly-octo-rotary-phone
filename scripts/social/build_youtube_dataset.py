"""Combine every YouTube output into one analysis dataset (metadata and counts only).

Inputs (all committed):
  data/deepfakes/youtube_<run>_videos.csv / _channels.csv   discovery runs
  data/deepfakes/factcheck_youtube_seeds_2018_2024.csv       fact-checked videos
  scripts/social/seeds/comma_youtube_videos.csv             ComMA annotated videos
  data/social_summary/youtube_<tag>_per_video.csv            comment counts of seed runs
  data/deepfakes/youtube_seed_video_meta.csv                 seed-video metadata
                                                             (--fetch-seed-meta, ~30 API units)
Outputs, data/youtube_dataset/:
  videos.csv    one row per video, all sources, uniform flags
  channels.csv  one row per channel
  panel_year.csv  year x source counts (2018-2024)
  youtube_dataset.xlsx  the three tables plus a README sheet

Usage:
  python scripts/social/build_youtube_dataset.py [--fetch-seed-meta]
"""
import argparse
import glob
import os
import re

import pandas as pd

from common import REPO, new_session
from youtube_comments import QuotaExceeded, call
from youtube_discover import AI_CUE

DF = REPO / "data" / "deepfakes"
SUM = REPO / "data" / "social_summary"
OUT = REPO / "data" / "youtube_dataset"
SEED_META = DF / "youtube_seed_video_meta.csv"

SEXUAL = re.compile(
    r"\bhot\b|sexy|\bsex\b|bikini|lingerie|\bnude|naked|nudify|undress|\b18\s*\+|adult|kiss|seduc|"
    r"\bbhabhi\b|obscene|\bmms\b|porn|sextortion|ai\s*(?:girl|model|beauty|lookbook|influencer)|"
    r"#ai(?:girl|model|beauty)|lookbook|सेक्सी|सेक्स|हॉट|नंगी|अश्लील|एमएमएस", re.I)
EXPLICIT = re.compile(
    r"\bhot\b|sexy|\bsex\b|bikini|lingerie|\bnude|naked|nudify|undress|\b18\s*\+|adult|seduc|"
    r"\bbhabhi\b|obscene|\bmms\b|porn|transparent|see\s*through|wet\s*saree|curvy|cleavage|"
    r"सेक्सी|सेक्स|हॉट|नंगी|अश्लील", re.I)
# news / awareness framing: reporting on harm rather than the content itself
NEWS = re.compile(r"\bnews\b|fir\b|arrest|police|complaint|cyber\s*crime|awareness|fact\s*check|"
                  r"खबर|गिरफ्तार|पुलिस|शिकायत|मुकदमा|सच", re.I)

VCOLS = ["video_id", "published_at", "year", "title", "channel_id", "channel_title", "country",
         "language", "views", "comments", "subscribers", "self_labelled", "ai_cue", "ai_cue_terms"]


def fetch_seed_meta(ids):
    s, rows = new_session(), []
    try:
        for i in range(0, len(ids), 50):
            res = call(s, "videos", part="snippet,statistics", id=",".join(ids[i:i + 50]))
            for v in res.get("items", []):
                sn, st = v["snippet"], v.get("statistics", {})
                rows.append({"video_id": v["id"], "published_at": sn.get("publishedAt"),
                             "title": sn.get("title"), "channel_id": sn.get("channelId"),
                             "channel_title": sn.get("channelTitle"),
                             "language": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "",
                             "views": st.get("viewCount"), "comments": st.get("commentCount"),
                             "blob": " ".join([sn.get("title", ""), sn.get("description", "")[:2000],
                                               " ".join(sn.get("tags", []))])})
        meta = pd.DataFrame(rows)
        chs = meta.channel_id.dropna().unique().tolist()
        cr = []
        for i in range(0, len(chs), 50):
            res = call(s, "channels", part="snippet,statistics", id=",".join(chs[i:i + 50]))
            cr += [{"channel_id": c["id"], "country": c["snippet"].get("country", ""),
                    "subscribers": c.get("statistics", {}).get("subscriberCount")}
                   for c in res.get("items", [])]
    except QuotaExceeded:
        print("quota exceeded: seed metadata not fetched; rerun tomorrow")
        return
    meta = meta.merge(pd.DataFrame(cr), on="channel_id", how="left")
    meta["ai_cue_terms"] = meta.blob.map(
        lambda b: "; ".join(sorted({m.group(0).lower() for m in AI_CUE.finditer(b)}))[:200])
    meta["ai_cue"] = meta.ai_cue_terms.ne("").astype(int)
    meta.drop(columns="blob").to_csv(SEED_META, index=False)
    print(f"seed metadata: {len(meta)} of {len(ids)} videos -> {SEED_META.relative_to(REPO)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch-seed-meta", action="store_true")
    a = ap.parse_args()

    fc = pd.read_csv(DF / "factcheck_youtube_seeds_2018_2024.csv", dtype={"video_id": str})
    cm = pd.read_csv(REPO / "scripts/social/seeds/comma_youtube_videos.csv", dtype={"video_id": str})
    if a.fetch_seed_meta:
        fetch_seed_meta(sorted(set(fc.video_id) | set(cm.video_id)))

    # --- discovery runs: one row per (run, video) first, then collapse to video ---
    parts = []
    for f in sorted(glob.glob(str(DF / "youtube_*_videos.csv"))):
        run = os.path.basename(f)[len("youtube_"):-len("_videos.csv")]
        d = pd.read_csv(f, dtype={"video_id": str})
        d["source"] = "discovery:" + run
        parts.append(d)
    disc = pd.concat(parts, ignore_index=True)

    seeds = []
    if SEED_META.exists():
        sm = pd.read_csv(SEED_META, dtype={"video_id": str})
    else:
        sm = pd.DataFrame(columns=["video_id"])
    fcv = fc.groupby("video_id").agg(
        factcheck_kind=("kind", lambda x: "; ".join(sorted(set(x.dropna())))),
        factcheck_mentions_woman=("mentions_woman", "max"),
        factcheck_publishers=("publisher", lambda x: "; ".join(sorted(set(x.dropna())))),
        factcheck_first_date=("factcheck_date", "min"),
        factcheck_link_role=("link_role", lambda x: "; ".join(sorted(set(x.dropna())))),
        oembed_status=("yt_status", "first"), fallback_title=("yt_title", "first"),
        fallback_channel=("yt_channel", "first")).reset_index()
    fcv["source"] = "seed:factcheck"
    cmv = cm[["video_id", "comments_annotated", "sexual_threat"]].rename(
        columns={"comments_annotated": "comma_comments_annotated",
                 "sexual_threat": "comma_sexual_threat_comments"})
    cmv["source"] = "seed:comma"
    for s in (fcv, cmv):
        s = s.merge(sm, on="video_id", how="left")
        if "fallback_title" in s:
            s["title"] = s.title.fillna(s.fallback_title)
            s["channel_title"] = s.channel_title.fillna(s.fallback_channel)
            s = s.drop(columns=["fallback_title", "fallback_channel"])
        seeds.append(s)
    allrows = pd.concat([disc] + seeds, ignore_index=True)
    allrows["year"] = pd.to_numeric(allrows.published_at.astype(str).str[:4], errors="coerce").astype("Int64")

    agg = {c: "first" for c in VCOLS[1:] if c in allrows}
    agg.update({"source": lambda x: "; ".join(sorted(set(x))),
                "queries": lambda x: "; ".join(sorted(set("; ".join(x.dropna()).split("; ")) - {""})),
                "debunk_comments": "max", "comments_scanned": "max"})
    for c in ["factcheck_kind", "factcheck_mentions_woman", "factcheck_publishers",
              "factcheck_first_date", "factcheck_link_role", "oembed_status",
              "comma_comments_annotated", "comma_sexual_threat_comments"]:
        agg[c] = "first"
    # prefer rows that carry API metadata when a video appears in several sources
    allrows = allrows.sort_values("published_at", na_position="last")
    v = allrows.groupby("video_id").agg(agg).reset_index()

    for name, flag in [("in_discovery", "discovery:"), ("in_factcheck_seeds", "seed:factcheck"),
                       ("in_comma_seeds", "seed:comma")]:
        v[name] = v.source.str.contains(flag, regex=False).astype(int)
    v["api_metadata"] = v.published_at.notna().astype(int)
    v["channel_in_india"] = v.country.eq("IN").astype(int)
    t = v.title.fillna("")
    v["ai_cue"] = v.ai_cue.fillna(t.str.contains(AI_CUE).astype(int)).astype(int)
    v["sexual_title_flag"] = t.str.contains(SEXUAL).astype(int)
    v["explicit_title_flag"] = t.str.contains(EXPLICIT).astype(int)
    v["news_framing_flag"] = t.str.contains(NEWS).astype(int)
    v["debunk_share"] = (v.debunk_comments / v.comments_scanned).round(3)

    # comment-collection counts for seed videos (no text)
    cc = []
    for tag in ("comma_seeds", "factcheck_seeds"):
        p = SUM / f"youtube_{tag}_per_video.csv"
        if p.exists():
            cc.append(pd.read_csv(p, dtype={"video_id": str})[
                ["video_id", "available", "comments_status", "comments", "rape_lexicon",
                 "hinglish_threat_lexicon", "hinglish"]])
    if cc:
        cc = pd.concat(cc).sort_values("comments", ascending=False).drop_duplicates("video_id")
        cc = cc.rename(columns={"available": "seed_available", "comments_status": "seed_comments_status",
                                "comments": "collected_comments", "rape_lexicon": "collected_rape_lexicon",
                                "hinglish_threat_lexicon": "collected_hinglish_threat_lexicon",
                                "hinglish": "collected_hinglish"})
        v = v.merge(cc, on="video_id", how="left")
        v["collected_rape_lexicon_rate"] = (v.collected_rape_lexicon / v.collected_comments).round(4)

    for c in ("views", "comments", "subscribers"):
        v[c] = pd.to_numeric(v[c], errors="coerce")
    v = v.sort_values(["year", "video_id"])

    # --- channels ---
    ch = []
    for f in sorted(glob.glob(str(DF / "youtube_*_channels.csv"))):
        ch.append(pd.read_csv(f))
    ch = pd.concat(ch, ignore_index=True)
    prof = ch.dropna(subset=["recent_ai_share"]).sort_values("recent_uploads_checked", ascending=False)
    ch = ch.groupby("channel_id").agg(channel_title=("channel_title", "first"), country=("country", "first"),
                                      channel_created=("channel_created", "first"),
                                      subscribers=("subscribers", "max"),
                                      channel_videos=("channel_videos", "max")).reset_index()
    ch = ch.merge(prof.drop_duplicates("channel_id")[["channel_id", "recent_ai_share", "recent_uploads_checked"]],
                  on="channel_id", how="left")
    vc = v.groupby("channel_id").agg(
        n_videos=("video_id", "size"), n_ai_cue=("ai_cue", "sum"),
        n_sexual_title=("sexual_title_flag", "sum"), n_explicit_title=("explicit_title_flag", "sum"),
        n_factcheck_seed=("in_factcheck_seeds", "sum"), first_year=("year", "min"), last_year=("year", "max"),
        sources=("source", lambda x: "; ".join(sorted(set("; ".join(x).split("; ")))))).reset_index()
    ch = vc.merge(ch, on="channel_id", how="left")
    ch["in_india"] = ch.country.eq("IN").astype(int)
    ch["manually_verified"] = ""
    ch = ch.sort_values(["in_india", "n_ai_cue", "n_videos"], ascending=False)

    # --- year panel (discovery videos with API metadata, 2018-2024) ---
    rows = []
    vv = v[v.year.between(2018, 2024)]
    for src, sub in [("all_discovery", vv[vv.in_discovery == 1])] + [(s, vv[vv.source.str.contains(s, regex=False)]) for s in
                                     sorted(set("; ".join(vv.source).split("; ")))]:
        g = sub.groupby("year").agg(
            videos=("video_id", "size"), channel_in_india=("channel_in_india", "sum"),
            ai_cue=("ai_cue", "sum"), sexual_title=("sexual_title_flag", "sum"),
            explicit_title=("explicit_title_flag", "sum"),
            explicit_and_ai=("explicit_title_flag", lambda x: int((x & sub.loc[x.index, "ai_cue"]).sum())),
            explicit_ai_india=("explicit_title_flag", lambda x: int(
                (x & sub.loc[x.index, "ai_cue"] & sub.loc[x.index, "channel_in_india"]).sum())),
            views=("views", "sum"), debunk_comments=("debunk_comments", "sum"),
            comments_scanned=("comments_scanned", "sum")).reset_index()
        g.insert(0, "source", src)
        rows.append(g)
    panel = pd.concat(rows, ignore_index=True)
    panel["ai_cue_share"] = (panel.ai_cue / panel.videos).round(3)
    panel["debunk_share"] = (panel.debunk_comments / panel.comments_scanned.where(panel.comments_scanned > 0)).astype(float).round(3)

    OUT.mkdir(parents=True, exist_ok=True)
    v.to_csv(OUT / "videos.csv", index=False)
    ch.to_csv(OUT / "channels.csv", index=False)
    panel.to_csv(OUT / "panel_year.csv", index=False)
    readme = pd.DataFrame({"README": (OUT / "README.md").read_text().splitlines()}) \
        if (OUT / "README.md").exists() else pd.DataFrame({"README": [__doc__]})
    with pd.ExcelWriter(OUT / "youtube_dataset.xlsx") as xw:
        readme.to_excel(xw, sheet_name="README", index=False)
        v.to_excel(xw, sheet_name="videos", index=False)
        ch.to_excel(xw, sheet_name="channels", index=False)
        panel.to_excel(xw, sheet_name="panel_year", index=False)
    print(f"{len(v)} videos ({v.api_metadata.sum()} with API metadata), {len(ch)} channels, "
          f"{len(panel)} panel rows -> {OUT.relative_to(REPO)}")
    print(panel[panel.source == "all_discovery"].to_string(index=False))


if __name__ == "__main__":
    main()
