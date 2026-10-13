"""Which occupation classification (NCO-2004 or NCO-2015) does each PLFS round use?

Run after plfs_counts_v3.py (or plfs_cell_counts.py), from the same "PLFS Data"
folder; it reads the file and variable choices saved in detected_columns.csv.

Test: code 251 ("software and applications developers") exists only in NCO-2015;
in NCO-2004 software work sits in 213 ("computing professionals"), and there is
no 25x group at all. So a round with many 251s and few 213s uses NCO-2015, and
one with 213s but no 251s uses NCO-2004.

    python3 plfs_nco_check_v2.py > nco_version.txt

Output: per round, counts of 3-digit codes 213, 251, 413, the number of distinct
codes, and a verdict. Errors are written into the same output. No individual data.
"""

import traceback
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
SKIP = {"2021"}


def check(p):
    s = pd.read_stata(BASE / p["file"], columns=[p["nco"]], convert_categoricals=False)[p["nco"]]
    s = s.astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
    s = s[s.str.fullmatch(r"\d+")].str.zfill(3).str[:3]
    n = {c: int((s == c).sum()) for c in ("213", "251", "413")}
    if n["251"] > 0 and n["251"] >= n["213"]:
        verdict = "NCO-2015"
    elif n["251"] == 0 and n["213"] > 0:
        verdict = "NCO-2004"
    else:
        verdict = "unclear"
    return {"coded_workers": len(s), "n_213": n["213"], "n_251": n["251"], "n_413": n["413"],
            "distinct_codes": s.nunique(), "verdict": verdict}


def main():
    path = BASE / "detected_columns.csv"
    if not path.exists():
        print("detected_columns.csv not found: run plfs_counts_v3.py first, in this same folder.")
        return
    plans = pd.read_csv(path)
    rows = []
    for _, p in plans.iterrows():
        if p["round"] in SKIP or pd.isna(p["nco"]):
            continue
        try:
            rows.append({"round": p["round"], "variable": p["nco"], **check(p)})
        except Exception:
            rows.append({"round": p["round"], "variable": p["nco"], "verdict": "ERROR"})
            print(f"ERROR in {p['round']} ({p['file']}):")
            print(traceback.format_exc())
        print(f"checked {p['round']}", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(BASE / "nco_version.csv", index=False)
    print()
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
