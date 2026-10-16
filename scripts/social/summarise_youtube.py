"""Aggregate a youtube_comments.py seed run into shareable counts (no comment
text, no usernames) under data/social_summary/.

Writes, for a run tag:
  youtube_<tag>_per_video.csv   one row per seed video: available / comment status,
                                comments collected, keyword-flag counts
  youtube_<tag>_by_group.csv    the same counts summed by each --group-by column
                                (a video linked from several fact-checks counts once
                                in every group it belongs to)

Usage:
  python scripts/social/summarise_youtube.py --tag factcheck_seeds \
      --seed-file data/deepfakes/factcheck_youtube_seeds_2018_2024.csv \
      --group-by kind mentions_woman
"""
import argparse
import glob

import pandas as pd

from common import OUT, REPO

FLAGS = ["rape_lexicon", "hinglish_threat_lexicon", "hinglish"]
SUMMARY = REPO / "data" / "social_summary"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--seed-file", required=True)
    ap.add_argument("--group-by", nargs="*", default=[])
    a = ap.parse_args()

    files = sorted(glob.glob(str(OUT / "youtube" / f"youtube_{a.tag}_2*.csv.gz")))
    com = pd.concat([pd.read_csv(f, usecols=["item_id", "thread_id", "parent_id"] + FLAGS)
                     for f in files]).drop_duplicates("item_id") if files else \
        pd.DataFrame(columns=["item_id", "thread_id", "parent_id"] + FLAGS)
    com["top_level"] = (com.parent_id == com.thread_id).astype(int)
    per = com.groupby("thread_id").agg(comments=("item_id", "size"), top_level=("top_level", "sum"),
                                       **{f: (f, "sum") for f in FLAGS}).reset_index() \
        .rename(columns={"thread_id": "video_id"})

    status = pd.read_csv(OUT / "youtube" / f"youtube_{a.tag}_video_status.csv")
    status = status.drop_duplicates("video_id", keep="last")[["video_id", "available", "comments_status"]]
    per = status.merge(per, on="video_id", how="left")
    per[["comments", "top_level"] + FLAGS] = per[["comments", "top_level"] + FLAGS].fillna(0).astype(int)
    for f in FLAGS:
        per[f"any_{f}"] = (per[f] > 0).astype(int)

    seeds = pd.read_csv(a.seed_file, dtype={"video_id": str})
    if "sexual_threat" in seeds:  # ComMA seeds: did annotators find any sexual threat?
        seeds["comma_sexual_threat_video"] = (seeds.sexual_threat > 0).astype(int)
    keep = ["video_id"] + [c for c in seeds.columns if c in
                           ("comments_annotated", "sexual_threat", "kind", "mentions_woman",
                            "publisher", "year", "factcheck_url")]
    first = seeds[keep].groupby("video_id").agg(
        lambda x: "; ".join(sorted({str(v) for v in x.dropna()}))).reset_index()
    out = first.merge(per, on="video_id", how="left")

    SUMMARY.mkdir(parents=True, exist_ok=True)
    out.to_csv(SUMMARY / f"youtube_{a.tag}_per_video.csv", index=False)

    def agg(df):
        return pd.Series({"videos": df.video_id.nunique(),
                          "available": int(df.available.eq(1).sum()),
                          "removed_or_private": int(df.available.eq(0).sum()),
                          "comments_disabled": int(df.comments_status.eq("disabled_or_error").sum()),
                          "not_collected_quota": int(df.comments_status.eq("not_collected_quota").sum()),
                          "comments": int(df.comments.sum()),
                          **{f: int(df[f].sum()) for f in FLAGS},
                          **{f"videos_with_{f}": int(df[f"any_{f}"].sum()) for f in FLAGS}})

    tables = [agg(per.fillna({"available": 0})).to_frame().T.assign(group_by="all", group="all")]
    for g in a.group_by:
        vids = per.merge(seeds[["video_id", g]].drop_duplicates(), on="video_id", how="left")
        t = vids.groupby(g).apply(agg, include_groups=False).reset_index().rename(columns={g: "group"})
        tables.append(t.assign(group_by=g))
    by = pd.concat(tables, ignore_index=True)
    by = by[["group_by", "group"] + [c for c in by.columns if c not in ("group_by", "group")]]
    by.to_csv(SUMMARY / f"youtube_{a.tag}_by_group.csv", index=False)
    print(by.to_string(index=False))


if __name__ == "__main__":
    main()
