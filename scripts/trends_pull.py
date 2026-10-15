"""Pull Google Trends interest in AI image-abuse tools and related harms for India.

Run this on your own computer (Google blocks most cloud servers):

    pip install pytrends pandas
    python scripts/trends_pull.py --out data/external/google_trends

It writes, under --out:
    national_monthly.csv   India, one row per month x term (2019-01 onwards), per sample
    state_yearly.csv       State/UT x year x term, per sample (cross-state comparison within a year)
    state_monthly.csv      State/UT x month x term for the CORE terms (--state-monthly), per sample
    raw/                   every response as returned, so nothing needs re-downloading
Re-running skips requests already saved in raw/, so if Google starts refusing (HTTP 429) just stop,
wait an hour, and run the same command again.

How to read Google Trends numbers
- Every value is a 0-100 index *within one request*: 100 = the highest point in that request.
  Terms pulled together in one request are comparable with each other; separate requests are not.
- interest_by_region gives, for one period, each state's share of searches that were for the term,
  scaled so the top state = 100. Cross-state comparisons are valid within a year; across years use
  year fixed effects (the regressions do) or the national series.
- Google samples its data, so the same request can return slightly different numbers. --samples N
  repeats each request (on different days is best) and the analysis averages them.
"""
import argparse, hashlib, json, os, random, time
from datetime import date

import pandas as pd

# Terms are grouped so that each request has at most 5 terms (Google's limit). Edit freely: add Hindi
# or regional-language terms and app names you see in news or complaints. Keep the group names.
GROUPS = {
    # Demand for AI "undressing" / nudify tools: the closest proxy for exposure to AI sexual abuse.
    "nudify": ["nudify", "undress ai", "clothoff", "deepnude", "ai nude"],
    # Deepfake / face-swap tools (dual use: also entertainment).
    "deepfake_tools": ["deepfake", "face swap", "deepfake app", "faceswap", "deepfake video"],
    # General generative-AI adoption (control / timing).
    "genai_general": ["chatgpt", "grok", "ai image generator", "gemini ai", "midjourney"],
    # Victim-side: looking for help or reporting.
    "harm_help": ["morphed photo", "sextortion", "cyber crime complaint", "deepfake complaint", "cybercrime.gov.in"],
    # Hindi / Hinglish victim-side terms (check spellings people actually use and refine).
    "harm_help_hi": ["फोटो मॉर्फ", "अश्लील वीडियो ब्लैकमेल", "साइबर क्राइम शिकायत", "photo morph karke", "fake photo viral"],
}
CORE_TERMS = ["nudify", "deepfake", "morphed photo", "sextortion", "chatgpt"]
START = "2019-01-01"


def cache_path(raw, kind, payload):
    h = hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return os.path.join(raw, f"{kind}_{h}.json")


def fetch(pytrends, raw, kind, payload, wait):
    """One Trends request, cached on disk, with backoff on 429."""
    path = cache_path(raw, kind, payload)
    if os.path.exists(path):
        return pd.read_json(path, orient="split")
    for attempt in range(6):
        try:
            pytrends.build_payload(payload["terms"], geo=payload["geo"], timeframe=payload["timeframe"])
            if kind == "region":
                df = pytrends.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=True)
            else:
                df = pytrends.interest_over_time()
                df = df.drop(columns=["isPartial"], errors="ignore")
            df.to_json(path, orient="split", force_ascii=False, date_format="iso")
            time.sleep(wait + random.uniform(0, wait / 2))
            return df
        except Exception as e:  # 429 / transient errors
            pause = min(60 * 2 ** attempt, 1800)
            print(f"  {type(e).__name__}: {str(e)[:80]} -> waiting {pause}s", flush=True)
            time.sleep(pause)
    raise RuntimeError(f"gave up on {payload}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/external/google_trends")
    ap.add_argument("--samples", type=int, default=1, help="repeat each request N times (label: sample)")
    ap.add_argument("--sample-id", type=int, default=None, help="label for this run's sample (e.g. run once per day with 1, 2, 3)")
    ap.add_argument("--end", default=date.today().isoformat())
    ap.add_argument("--wait", type=float, default=20, help="seconds between requests")
    ap.add_argument("--state-monthly", action="store_true", help="also pull state x month series for CORE_TERMS (36 x 5 requests)")
    args = ap.parse_args()

    from pytrends.request import TrendReq  # imported here so --help works without it
    raw = os.path.join(args.out, "raw")
    os.makedirs(raw, exist_ok=True)
    py = TrendReq(hl="en-US", tz=-330, timeout=(10, 30))  # no retries=: breaks with urllib3 2.x
    end_year = int(args.end[:4])
    samples = [args.sample_id] if args.sample_id else list(range(1, args.samples + 1))
    nat, reg, stm = [], [], []
    for s in samples:
        for g, terms in GROUPS.items():
            # 1) national monthly series (a range > 5 years returns monthly points)
            p = {"terms": terms, "geo": "IN", "timeframe": f"{START} {args.end}", "sample": s}
            print(f"[sample {s}] national {g}", flush=True)
            df = fetch(py, raw, "time", p, args.wait)
            for t in terms:
                if t in df:
                    nat += [{"sample": s, "group": g, "term": t, "month": str(i)[:7], "value": v}
                            for i, v in df[t].items()]
            # 2) state x year cross-sections
            for y in range(2019, end_year + 1):
                tf = f"{y}-01-01 {min(f'{y}-12-31', args.end)}"
                p = {"terms": terms, "geo": "IN", "timeframe": tf, "sample": s}
                print(f"[sample {s}] states {g} {y}", flush=True)
                df = fetch(py, raw, "region", p, args.wait)
                for t in terms:
                    if t in df:
                        reg += [{"sample": s, "group": g, "term": t, "year": y, "state": name,
                                 "geo_code": df.loc[name, "geoCode"] if "geoCode" in df else "", "value": v}
                                for name, v in df[t].items()]
        if args.state_monthly:
            # 3) per-state monthly series for core terms: within-state timing (0-100 per state)
            codes = sorted({r["geo_code"] for r in reg if r["geo_code"]})
            for code in codes:
                for t in CORE_TERMS:
                    p = {"terms": [t], "geo": code, "timeframe": f"{START} {args.end}", "sample": s}
                    print(f"[sample {s}] {code} {t}", flush=True)
                    df = fetch(py, raw, "time", p, args.wait)
                    if t in df:
                        stm += [{"sample": s, "geo_code": code, "term": t, "month": str(i)[:7], "value": v}
                                for i, v in df[t].items()]

    def save(rows, name):
        if not rows:
            return
        path = os.path.join(args.out, name)
        new = pd.DataFrame(rows)
        if os.path.exists(path):  # keep earlier samples
            old = pd.read_csv(path)
            new = pd.concat([old[~old["sample"].isin(new["sample"].unique())], new])
        new.to_csv(path, index=False)
        print("wrote", path, len(new), "rows")

    save(nat, "national_monthly.csv")
    save(reg, "state_yearly.csv")
    save(stm, "state_monthly.csv")


if __name__ == "__main__":
    main()
