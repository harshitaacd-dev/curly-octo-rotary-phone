"""Post-level metadata of sexual 'fakes' / morph / deepfake activity aimed at
Indian women on Reddit, 2018-2024 (perpetrator side). Ethics-approved study.

Data minimisation (enforced in code)
  * Requested fields are ONLY: id, created_utc, subreddit, title,
    link_flair_text, over_18, num_comments, score. Usernames, media URLs,
    thumbnails, previews, post bodies and permalinks are never requested
    (FORBIDDEN is asserted absent) and media links are never followed.
  * Titles are kept only in the git-ignored raw file, with the community
    replaced by its code. Rows with a minor indicator have the title dropped
    before anything is saved; they are only counted and reported.
  * Committed outputs are counts only.

Inputs
  (a) every 2018-2024 post in the India-group communities found by
      reddit_fakes_communities.py (code list in data/social_raw/reddit/)
  (b) solicitation-term post search in the core Indian subreddits
      (reddit_trend.CORE), normalised by their monthly post totals

Removal status is not a selectable archive field, so enforcement is measured
at community level (bans / inactivity, reddit_fakes_communities.py).

Outputs
  data/social_raw/reddit/fakes_posts_2018_2024.csv.gz            (git-ignored)
  data/social_summary/reddit_fakes_posts_monthly.csv
  data/social_summary/reddit_fakes_posts_hour_weekday.csv
  data/social_summary/reddit_fakes_posts_place_year.csv
  data/social_summary/reddit_solicitation_core_monthly.csv

Usage
  python scripts/social/reddit_fakes_posts.py                 # both parts
  python scripts/social/reddit_fakes_posts.py --part core     # (b) only
  python scripts/social/reddit_fakes_posts.py --codes C001 --years 2023   # smoke test
"""
import argparse
import re
import time
import warnings

import pandas as pd

from common import OUT as RAW, REPO, get_json, new_session
from reddit_trend import CORE, series

ARCTIC = "https://arctic-shift.photon-reddit.com/api"
SUMMARY = REPO / "data" / "social_summary"
warnings.filterwarnings("ignore", "This pattern is interpreted as a regular expression")
FIELDS = "id,created_utc,subreddit,title,link_flair_text,over_18,num_comments,score"
FORBIDDEN = {"author", "author_fullname", "url", "selftext", "thumbnail", "preview", "media",
             "media_metadata", "secure_media", "permalink", "url_overridden_by_dest", "gallery_data"}
SOLICIT_TERMS = ["morph", "morphed", "fakes", "deepfake", "nudify", "faceswap"]

SOLICIT = re.compile(
    r"\breq(uest)?s?\b|can (any|some)\s*(one|body)|any\s*one\s+(make|do|morph|edit|fake)|"
    r"\bpl(ea)?se?\b|\bpls\b|\bdm\b|\bpaid\b|\bpay(ing)?\b|commission|\brs\.?\s*\d|₹|\$\s*\d|"
    r"telegram|\btg\b|discord|\bkik\b|\binbox\b|who can|need (a |someone)|make (her|a|me)", re.I)
PRIVATE = re.compile(
    r"\b(my|meri|mere|our)\s+(ex|gf|girl\s*friend|wife|sister|cousin|classmate|colleague|friend|"
    r"neighbou?r|crush|teacher|senior|junior|boss|bhabhi|aunty|landlady|maid)\b|"
    r"\b(classmate|colleague|neighbou?r|ex[\s-]*gf|office (girl|colleague)|college (girl|crush)|"
    r"hostel|tuition|known girl|real girl)\b", re.I)
INFLUENCER = re.compile(r"insta(gram)?|influencer|youtuber|tiktok|moj|josh app|reels?|onlyfans|streamer", re.I)
CELEB = re.compile(r"actress|heroine|celeb|bollywood|tollywood|kollywood|mollywood|serial|tv\b|anchor|"
                   r"singer|cricketer|model|star\b", re.I)
AI = re.compile(r"\bai\b|a\.i\.|deep\s*-?fake|nudif|face\s*-?swap|undress|generated|stable diffusion|midjourney", re.I)
MINOR = re.compile(r"\bschool|\bteen|\bunder\s*-?age|\bminor\b|\bclass\s*(\d{1,2})\b|\b(1[0-7])\s*(yo|y/o|yrs?|years?)\b|"
                   r"\bschoolgirl|\bstudent of class|\bkid\b|\bchild", re.I)

PLACES = {  # term -> state / UT
    "Kerala": r"kerala|mallu|kochi|cochin|trivandrum|thiruvananthapuram|kozhikode|calicut|thrissur",
    "Tamil Nadu": r"tamil|chennai|madras|coimbatore|madurai|trichy|salem",
    "Karnataka": r"kannada|karnataka|bangalore|bengaluru|mysore|mysuru|mangalore",
    "Andhra Pradesh": r"andhra|vizag|visakhapatnam|vijayawada|guntur|tirupati",
    "Telangana": r"telangana|hyderabad|secunderabad|warangal",
    "Maharashtra": r"marathi|maharashtra|mumbai|bombay|pune|nagpur|nashik|thane",
    "Gujarat": r"gujarat|gujju|ahmedabad|surat|vadodara|baroda|rajkot",
    "Delhi": r"\bdelhi|\bncr\b|noida|gurgaon|gurugram|faridabad|ghaziabad",
    "Uttar Pradesh": r"\bup\b girl|uttar pradesh|lucknow|kanpur|varanasi|banaras|agra|meerut|allahabad|prayagraj",
    "Bihar": r"bihar|patna|bhojpuri",
    "West Bengal": r"bengal|bengali|bangla|kolkata|calcutta|siliguri|durgapur",
    "Punjab": r"punjab|amritsar|ludhiana|jalandhar|mohali",
    "Haryana": r"haryana|haryanvi|rohtak|panipat|hisar",
    "Rajasthan": r"rajasthan|jaipur|jodhpur|udaipur|kota",
    "Madhya Pradesh": r"madhya pradesh|\bmp\b girl|indore|bhopal|gwalior|jabalpur",
    "Odisha": r"odisha|orissa|odia|bhubaneswar|cuttack",
    "Assam / North-East": r"assam|guwahati|assamese|manipur|meghalaya|shillong|nagaland|mizoram|northeast|north east",
    "Jharkhand": r"jharkhand|ranchi|jamshedpur",
    "Chhattisgarh": r"chhattisgarh|raipur",
    "Goa": r"\bgoa\b",
    "Jammu & Kashmir": r"kashmir|srinagar|jammu",
    "Uttarakhand / Himachal": r"uttarakhand|dehradun|himachal|shimla",
}
PLACE_RE = {k: re.compile(v, re.I) for k, v in PLACES.items()}


def fetch(s, sub, lo, hi, query=None, depth=0):
    """All posts in [lo, hi) for a subreddit (optionally matching query); halves window on timeout."""
    out, cursor = [], lo
    while True:
        p = {"subreddit": sub, "limit": 100, "sort": "asc", "after": cursor, "before": hi, "fields": FIELDS}
        if query:
            p["query"] = query
        try:
            data = get_json(s, f"{ARCTIC}/posts/search", p, tries=4, wait=3).get("data") or []
        except RuntimeError:
            if hi - lo > 15 * 86400 and depth < 6:
                mid = (lo + hi) // 2
                return out + fetch(s, sub, cursor, mid, query, depth + 1) + fetch(s, sub, mid, hi, query, depth + 1)
            print(f"    gave up: r/{sub} {query or ''} {lo}-{hi}")
            return out
        for r in data:
            bad = FORBIDDEN & set(r)
            assert not bad, f"forbidden fields returned: {bad}"
        out += data
        time.sleep(1.5)
        if len(data) < 100:
            return out
        cursor = int(data[-1]["created_utc"]) + 1


def classify(df):
    t = df.title.fillna("")
    df["minor_indicator"] = t.str.contains(MINOR).astype(int)
    flair = df.get("link_flair_text", pd.Series("", index=df.index)).fillna("")
    df["solicitation"] = (t.str.contains(SOLICIT) | flair.str.contains(r"req", case=False)).astype(int)
    df["ai_wording"] = t.str.contains(AI).astype(int)
    df["target_type"] = "generic/unspecified"
    df.loc[t.str.contains(CELEB), "target_type"] = "celebrity"
    df.loc[t.str.contains(INFLUENCER), "target_type"] = "influencer"
    df.loc[t.str.contains(PRIVATE), "target_type"] = "private acquaintance"
    df["place"] = t.map(lambda x: next((k for k, r in PLACE_RE.items() if r.search(x)), ""))
    # Title mentions only: the link domain is not available without requesting the media URL.
    df["migration"] = t.str.contains(r"telegram|\btg\b|t\.me/|discord|\bkik\b|whats\s*app", case=False).astype(int)
    ist = pd.to_datetime(df.created_utc, unit="s", utc=True).dt.tz_convert("Asia/Kolkata")
    df["month"], df["year"] = ist.dt.strftime("%Y-%m"), ist.dt.strftime("%Y")
    df["hour_ist"], df["weekday"] = ist.dt.hour, ist.dt.day_name()
    df.loc[df.minor_indicator == 1, "title"] = ""  # never keep these titles
    return df


def years_bounds(years):
    for y in years:
        yield (int(pd.Timestamp(f"{y}-01-01", tz="Asia/Kolkata").timestamp()),
               int(pd.Timestamp(f"{y + 1}-01-01", tz="Asia/Kolkata").timestamp()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["all", "communities", "core"], default="all")
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2018, 2025)))
    ap.add_argument("--codes", nargs="*", help="only these community codes (smoke test)")
    ap.add_argument("--core", nargs="*", default=CORE)
    a = ap.parse_args()
    s = new_session()
    tag = f"{min(a.years)}_{max(a.years)}"
    rows = []

    if a.part in ("all", "communities"):
        codes = pd.read_csv(RAW / "reddit" / "fakes_community_codes.csv")
        meta = pd.read_csv(SUMMARY / "reddit_fakes_communities.csv")
        c = codes.merge(meta, on="code")
        c = c[c.group.eq("india")]
        if a.codes:
            c = c[c.code.isin(a.codes)]
        c = c[c.total_posts.fillna(0) > 0]
        for _, r in c.iterrows():
            n = 0
            for lo, hi in years_bounds(a.years):
                for p in fetch(s, r["name"], lo, hi):
                    p.update(source="community", code=r.code, region_name=r.region,
                             community_target=r.target_type)
                    rows.append(p)
                    n += 1
            print(f"  {r.code} ({r.region or 'n/a'}): {n} posts")

    if a.part in ("all", "core"):
        for sub in a.core:
            n = 0
            for term in SOLICIT_TERMS:
                for lo, hi in years_bounds(a.years):
                    for p in fetch(s, sub, lo, hi, query=term):
                        p.update(source="core", code=f"core:{sub}", region_name="", community_target="")
                        rows.append(p)
                        n += 1
            print(f"  r/{sub}: {n} term hits")

    df = pd.DataFrame(rows)
    if df.empty:
        print("nothing collected")
        return
    df = df.drop_duplicates(["source", "id"])
    assert not FORBIDDEN & set(df.columns)
    df = classify(df)
    core_rows = df.source.eq("core")
    # core subreddits: only keep hits whose title is actually about sexual fakes/morphs
    sexual = df.title.str.contains(r"nud|nsfw|porn|obscene|naked|sexy|hot\b|lewd|xxx|explicit|vulgar|"
                                   r"fake|morph|deepfake|undress", case=False, na=False)
    df = df[~core_rows | sexual | (df.minor_indicator == 1)]
    df.loc[df.source.eq("community"), "subreddit"] = ""  # community identified by code only

    (RAW / "reddit").mkdir(parents=True, exist_ok=True)
    keep = ["source", "code", "subreddit", "id", "month", "year", "hour_ist", "weekday", "title",
            "link_flair_text", "over_18", "num_comments", "score", "solicitation",
            "target_type", "community_target", "ai_wording", "place", "region_name", "migration",
            "minor_indicator"]
    df[keep].to_csv(RAW / "reddit" / f"fakes_posts_{tag}.csv.gz", index=False, compression="gzip")

    SUMMARY.mkdir(parents=True, exist_ok=True)
    g = df.groupby(["source", "month", "region_name", "target_type"]).agg(
        posts=("id", "size"), solicitation=("solicitation", "sum"), ai_wording=("ai_wording", "sum"),
        migration=("migration", "sum"),
        minor_indicator=("minor_indicator", "sum")).reset_index()
    g.to_csv(SUMMARY / f"reddit_fakes_posts_monthly.csv", index=False)
    df.groupby(["source", "weekday", "hour_ist"]).size().rename("posts").reset_index().to_csv(
        SUMMARY / "reddit_fakes_posts_hour_weekday.csv", index=False)
    df[df.place.ne("")].groupby(["source", "place", "year"]).size().rename("posts").reset_index().to_csv(
        SUMMARY / "reddit_fakes_posts_place_year.csv", index=False)

    if a.part in ("all", "core"):
        den = []
        for sub in a.core:
            for m, v in series(s, sub, "posts", f"{min(a.years)}-01-01", f"{max(a.years) + 1}-01-01").items():
                den.append({"subreddit": sub, "month": m, "total_posts": v})
        den = pd.DataFrame(den)
        hits = df[df.source.eq("core")].groupby(["subreddit", "month"]).agg(
            sexual_fake_posts=("id", "size"), solicitation=("solicitation", "sum")).reset_index()
        core = den.merge(hits, on=["subreddit", "month"], how="left").fillna(0)
        core.to_csv(SUMMARY / "reddit_solicitation_core_monthly.csv", index=False)

    # Report
    y = df.groupby(["source", "year"]).agg(
        posts=("id", "size"), solicitation=("solicitation", "mean"),
        migration=("migration", "mean"), ai_wording=("ai_wording", "mean")).round(3)
    print("\n", y.to_string())
    print("\ntarget type share:\n", pd.crosstab(df.year, df.target_type, normalize="index").round(3).to_string())
    print("\ntop places:\n", df[df.place.ne("")].place.value_counts().head(12).to_string())
    print("\nposts by IST hour:\n", df.hour_ist.value_counts().sort_index().to_string())
    mi = int(df.minor_indicator.sum())
    if mi:
        print(f"\n!! {mi} posts have a MINOR INDICATOR in the title (titles not stored). "
              f"Their ids are in the raw file (minor_indicator=1) for reporting under your "
              f"institution's protocol (e.g. NCMEC / India's cybercrime.gov.in).")


if __name__ == "__main__":
    main()
