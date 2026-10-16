"""Timeline of Reddit communities dedicated to sexual 'fakes' / morphs /
deepfakes of Indian women, 2018-2024 - from COMMUNITY-LEVEL METADATA ONLY.

No posts, titles, comments, authors, media URLs, descriptions or images are
requested. For each community the script uses only: name, creation date,
NSFW flag, type (public / restricted / private / banned...), subscriber count,
and the archive's monthly post and comment COUNTS (Arctic Shift time_series).

Steps
  1. Discover subreddits by name prefix (Arctic Shift subreddits/search) and
     keep names that combine an India / region / film-industry term with a
     fakes / morph / deepfake / nudify term (FAKE_RE + INDIA_RE). A global
     deepfake-porn group (no India term, NSFW) is kept as a comparison.
  2. Classify from the NAME only: region (Kerala, Tamil Nadu, ...), target type
     (celebrity vs non-celebrity women), and AI wording.
  3. Monthly post / comment counts 2015-2025 per community -> first and last
     active month (a proxy for creation-to-ban lifespan), peak, totals.

Outputs
  data/social_summary/reddit_fakes_communities.csv     one row per community,
      identified by a code (C001...), never by name, so the repo cannot serve
      as a directory to this material
  data/social_summary/reddit_fakes_monthly.csv         month x group x region counts
  data/social_summary/reddit_fakes_yearly.csv          yearly summary
  data/social_raw/reddit/fakes_community_codes.csv     code -> name (git-ignored)

Usage: python scripts/social/reddit_fakes_communities.py
"""
import re
import time

import pandas as pd

from common import OUT as RAW, REPO, get_json, new_session

ARCTIC = "https://arctic-shift.photon-reddit.com/api"
SUMMARY = REPO / "data" / "social_summary"

PREFIXES = [
    # specific
    "desifake", "desi_fake", "desideepfake", "desimorph", "desinud", "indianfake",
    "indian_fake", "indiancelebfake", "indianactressfake", "indiandeepfake", "indianmorph",
    "bollywoodfake", "bollyfake", "bollywooddeepfake", "tollywoodfake", "kollywoodfake",
    "mollywoodfake", "sandalwoodfake", "mallufake", "tamilfake", "telugufake", "kannadafake",
    "bengalifake", "punjabifake", "marathifake", "gujaratifake", "southindianfake",
    # broad (filtered by name below)
    "desi", "indian", "india", "bolly", "tolly", "kolly", "molly", "mallu", "tamil", "telugu",
    "kannada", "bengali", "bangla", "punjabi", "marathi", "gujju", "gujarati", "bhojpuri",
    "odia", "hindi", "southindian", "south_indian", "celebfake", "deepfake", "morph",
]

FAKE_RE = re.compile(r"fake|morph|deep_?fake|nudif|faceswap|face_?swap|edits?$|_edit", re.I)
INDIA_RE = re.compile(
    r"desi|indian|india|bolly|tolly|kolly|molly|sandalwood|mallu|tamil|telugu|kannada|bengali|"
    r"bangla|punjab|marathi|gujju|gujarat|bhojpuri|odia|hindi|southindian|south_indian|"
    r"bhabhi|aunty|kerala|chennai|mumbai|delhi|hyderabad|bangalore|kolkata", re.I)
REGION = [  # name term -> region label
    ("Kerala", r"mallu|molly|kerala"), ("Tamil Nadu", r"tamil|kolly|chennai"),
    ("Andhra Pradesh / Telangana", r"telugu|tolly|hyderabad"),
    ("Karnataka", r"kannada|sandalwood|bangalore"), ("West Bengal / Bangla", r"bengali|bangla|kolkata"),
    ("Punjab", r"punjab"), ("Maharashtra", r"marathi|mumbai"), ("Gujarat", r"gujju|gujarat"),
    ("Bihar / UP (Bhojpuri)", r"bhojpuri"), ("Odisha", r"odia"), ("Delhi", r"delhi"),
    ("South India (generic)", r"southindian|south_indian"),
    ("Hindi film (Bollywood)", r"bolly|hindi"), ("Pan-India (desi / indian)", r"desi|indian|india"),
]
CELEB_RE = re.compile(r"celeb|actress|bolly|tolly|kolly|molly|sandalwood|star|heroine|anchor|tv|serial|model", re.I)
NONCELEB_RE = re.compile(r"girl|aunty|bhabhi|college|insta|wife|gf|amateur|real|teen|school|office", re.I)
AI_RE = re.compile(r"deep_?fake|\bai|ai_|nudif|faceswap|face_?swap", re.I)


def region(name):
    return next((lab for lab, pat in REGION if re.search(pat, name, re.I)), "")


def discover(s):
    seen = {}
    for p in PREFIXES:
        d = get_json(s, f"{ARCTIC}/subreddits/search",
                     {"subreddit_prefix": p, "limit": 1000}, tries=4, wait=3).get("data") or []
        if len(d) >= 1000:
            print(f"  prefix '{p}': 1000 results (truncated; specific prefixes cover the rest)")
        for x in d:
            name = x.get("display_name") or ""
            india, fake, nsfw = bool(INDIA_RE.search(name)), bool(FAKE_RE.search(name)), bool(x.get("over18"))
            if fake and (india or nsfw):
                m = x.get("_meta") or {}
                seen[name.lower()] = {
                    "name": name, "group": "india" if india else "global_nsfw_deepfake",
                    "created": pd.Timestamp(x["created_utc"], unit="s").strftime("%Y-%m-%d") if x.get("created_utc") else "",
                    "over18": int(nsfw), "subreddit_type": x.get("subreddit_type", ""),
                    "quarantine": int(bool(x.get("quarantine"))), "subscribers": x.get("subscribers"),
                    "archive_posts": m.get("num_posts"), "archive_comments": m.get("num_comments"),
                }
        time.sleep(2)
    return pd.DataFrame(seen.values())


def monthly(s, name, kind):
    j = get_json(s, f"{ARCTIC}/time_series", {"key": f"r/{name}/{kind}/count", "precision": "month",
                                              "after": "2015-01-01", "before": "2026-01-01"}, tries=4, wait=3)
    time.sleep(1.5)
    return {pd.Timestamp(d["date"], unit="s").strftime("%Y-%m"): d["value"] for d in j.get("data") or []}


def main():
    s = new_session()
    c = discover(s)
    print(f"{len(c)} candidate communities ({(c.group == 'india').sum()} India-specific)")
    # India-specific communities need a sexual signal too: NSFW flag or explicit name term.
    c = c[(c.group == "global_nsfw_deepfake") | c.over18.eq(1) |
          c.name.str.contains(r"nud|nsfw|porn|xxx|hot|sexy|lewd|boob|ass", case=False)]
    c = c.sort_values(["group", "created", "name"]).reset_index(drop=True)
    c["code"] = [f"C{i + 1:03d}" for i in range(len(c))]
    c["region"] = c.name.map(region)
    c["target_type"] = c.name.map(lambda n: "celebrity" if CELEB_RE.search(n) else
                                  ("non-celebrity women" if NONCELEB_RE.search(n) else "unspecified"))
    c["ai_wording"] = c.name.str.contains(AI_RE).astype(int)

    rows = []
    for _, r in c.iterrows():
        posts, comments = monthly(s, r["name"], "posts"), monthly(s, r["name"], "comments")
        for m in sorted(set(posts) | set(comments)):
            rows.append({"code": r.code, "month": m, "posts": posts.get(m, 0), "comments": comments.get(m, 0)})
    ts = pd.DataFrame(rows, columns=["code", "month", "posts", "comments"])

    act = ts[ts.posts > 0].groupby("code").agg(first_active=("month", "min"), last_active=("month", "max"),
                                                active_months=("month", "nunique"),
                                                total_posts=("posts", "sum"))
    peak = ts.loc[ts.groupby("code").posts.idxmax(), ["code", "month", "posts"]].rename(
        columns={"month": "peak_month", "posts": "peak_posts"}).set_index("code") if len(ts) else None
    c = c.join(act, on="code")
    if peak is not None:
        c = c.join(peak, on="code")

    (RAW / "reddit").mkdir(parents=True, exist_ok=True)
    c[["code", "name"]].to_csv(RAW / "reddit" / "fakes_community_codes.csv", index=False)
    SUMMARY.mkdir(parents=True, exist_ok=True)
    pub = c.drop(columns=["name"])
    pub.to_csv(SUMMARY / "reddit_fakes_communities.csv", index=False)

    ts = ts.merge(c[["code", "group", "region", "target_type", "ai_wording"]], on="code")
    m = ts.groupby(["month", "group", "region", "target_type"]).agg(
        active_communities=("posts", lambda x: int((x > 0).sum())),
        posts=("posts", "sum"), comments=("comments", "sum")).reset_index()
    m.to_csv(SUMMARY / "reddit_fakes_monthly.csv", index=False)

    ts["year"] = ts.month.str[:4]
    first = c.dropna(subset=["first_active"]).assign(year=lambda d: d.first_active.str[:4])
    last = c.dropna(subset=["last_active"]).assign(year=lambda d: d.last_active.str[:4])
    y = ts.groupby(["group", "year"]).agg(
        active_communities=("code", lambda x: x[ts.loc[x.index, "posts"] > 0].nunique()),
        posts=("posts", "sum"), comments=("comments", "sum")).reset_index()
    y = y.merge(first.groupby(["group", "year"]).size().rename("new_communities").reset_index(),
                on=["group", "year"], how="left").merge(
        last.groupby(["group", "year"]).size().rename("went_inactive").reset_index(),
        on=["group", "year"], how="left").fillna({"new_communities": 0, "went_inactive": 0})
    y.to_csv(SUMMARY / "reddit_fakes_yearly.csv", index=False)

    print(pub.groupby("group").agg(n=("code", "size"), posts=("total_posts", "sum")).to_string())
    print(y[(y.year >= "2016") & (y.year <= "2025")].to_string(index=False))
    india = pub[pub.group == "india"]
    print("\nIndia communities by region:\n", india.region.value_counts().to_string())
    print("\nby target type:\n", india.target_type.value_counts().to_string())
    print("\nby type/status:\n", india.subreddit_type.value_counts().to_string())


if __name__ == "__main__":
    main()
