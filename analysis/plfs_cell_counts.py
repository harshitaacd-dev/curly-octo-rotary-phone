"""Day-1 feasibility check: how many women does PLFS record in data work?

Counts persons by sex in
  - occupation NCO-2015 3-digit 413 ("keyboard operators": typists, data entry)
  - industry NIC-2008 6311x (data processing, hosting and related activities)
  - the comparison group NIC 62xxx (IT services)
for each PLFS person file you point it at, unweighted and survey-weighted.

Usage
-----
1. Download each PLFS round from microdata.gov.in (free account). Keep the
   person-level first-visit file (e.g. FPER_FV.txt, PerV1.txt, CPERV1.txt)
   and that round's data layout Excel file.
2. For each round, open the layout file and copy the start position and width
   of the five fields below into ROUNDS. Field names differ across rounds,
   which is why positions are entered by hand rather than guessed.
3. Run:  python3 plfs_cell_counts.py
   Output: cell_counts.csv plus a printed table.

Rule of thumb: fewer than ~100 women per round in a cell means pool rounds
or widen the definition (NIC 63 + 82) before treating it as a paper section.
"""

import csv
import sys
from pathlib import Path

import pandas as pd

# Fill one entry per round. start = 1-based start column from the layout file.
# The values below are placeholders; replace every number with the layout's.
ROUNDS = {
    # "2017-18": {
    #     "file": "data/2017-18/FPER_FV.txt",
    #     "sex":    {"start": 0, "width": 1},   # 1 = male, 2 = female, 3 = transgender
    #     "age":    {"start": 0, "width": 3},
    #     "nco":    {"start": 0, "width": 3},   # usual principal status occupation (NCO-2015)
    #     "nic":    {"start": 0, "width": 5},   # usual principal status industry (NIC-2008)
    #     "weight": {"start": 0, "width": 10},  # multiplier; see README for the divisor
    #     "weight_divisor": 100,                # README states how to build the final weight
    # },
}

FIELDS = ["sex", "age", "nco", "nic", "weight"]


def read_round(spec):
    colspecs = [(spec[f]["start"] - 1, spec[f]["start"] - 1 + spec[f]["width"]) for f in FIELDS]
    df = pd.read_fwf(spec["file"], colspecs=colspecs, names=FIELDS, dtype=str, header=None)
    df = df.apply(lambda s: s.str.strip())
    df["w"] = pd.to_numeric(df["weight"], errors="coerce") / spec.get("weight_divisor", 100)
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    return df


def count_cells(df):
    work_age = df[(df["age"] >= 15) & (df["age"] <= 64)]
    cells = {
        "NCO 413 keyboard operators": work_age["nco"].str.startswith("413", na=False),
        "NIC 6311 data processing": work_age["nic"].str.startswith("6311", na=False),
        "NIC 62 IT services": work_age["nic"].str.startswith("62", na=False),
        "NIC 63 + 82 (wide definition)": work_age["nic"].str.match(r"^(63|82)", na=False),
    }
    rows = []
    for name, mask in cells.items():
        sub = work_age[mask]
        for code, label in (("1", "men"), ("2", "women")):
            s = sub[sub["sex"] == code]
            rows.append({"cell": name, "sex": label, "n_unweighted": len(s),
                         "n_weighted": round(s["w"].sum())})
    return rows


def main():
    if not ROUNDS:
        sys.exit("ROUNDS is empty: add each PLFS round's file path and field positions first.")
    out = []
    for rnd, spec in ROUNDS.items():
        if not Path(spec["file"]).exists():
            print(f"skip {rnd}: {spec['file']} not found")
            continue
        for row in count_cells(read_round(spec)):
            out.append({"round": rnd, **row})
    if not out:
        sys.exit("No files read.")
    table = pd.DataFrame(out)
    table.to_csv("cell_counts.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    print(table.pivot_table(index=["cell", "sex"], columns="round",
                            values="n_unweighted", aggfunc="sum").to_string())
    thin = table[(table["sex"] == "women") & (table["n_unweighted"] < 100)]
    if not thin.empty:
        print("\nCells with fewer than 100 women (pool rounds or widen):")
        print(thin[["round", "cell", "n_unweighted"]].to_string(index=False))


if __name__ == "__main__":
    main()
