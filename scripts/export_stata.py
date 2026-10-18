"""Write a Stata .dta copy of every CSV in datasets/ (and data/analysis/), next to the CSV.

Usage: python scripts/export_stata.py

Stata format 118 (Stata 14+), UTF-8. Stata variable names must be at most 32 characters and start with a
letter or underscore; longer or invalid names are shortened, and every variable label holds the original
CSV column name. Long text goes into strL columns. Files written: <name>.dta beside <name>.csv
(<name>.csv.gz -> <name>.dta).
"""
import glob, os, re

import pandas as pd

ROOTS = ["datasets", "data/analysis"]
# Text corpus, not regression data; as .dta it exceeds GitHub's 100 MB file limit.
SKIP = {"threat_corpus_full.csv.gz"}


def stata_names(cols):
    out, seen = {}, set()
    for c in cols:
        n = re.sub(r"[^A-Za-z0-9_]", "_", c)
        if not re.match(r"[A-Za-z_]", n):
            n = "v" + n
        n = n[:32]
        base, i = n, 1
        while n.lower() in seen:
            suffix = f"_{i}"
            n, i = base[:32 - len(suffix)] + suffix, i + 1
        seen.add(n.lower())
        out[c] = n
    return out


def convert(path):
    d = pd.read_csv(path, low_memory=False)
    names = stata_names(d.columns)
    d = d.rename(columns=names)
    labels = {new: old[:80] for old, new in names.items()}
    for c in d.columns:
        if d[c].dtype == bool:
            d[c] = d[c].astype("int8")
        elif d[c].dtype == object or str(d[c].dtype).startswith("str"):
            d[c] = d[c].astype(object).where(d[c].notna(), "").astype(str)
    strl = [c for c in d.columns if d[c].dtype == object and d[c].str.len().max() > 2045]
    out = re.sub(r"\.csv(\.gz)?$", ".dta", path)
    d.to_stata(out, write_index=False, version=118, variable_labels=labels, convert_strl=strl)
    renamed = sum(1 for k, v in names.items() if k != v)
    return out, len(d), renamed


def main():
    files = []
    for r in ROOTS:
        files += glob.glob(os.path.join(r, "**", "*.csv"), recursive=True)
        files += glob.glob(os.path.join(r, "**", "*.csv.gz"), recursive=True)
    for f in sorted(files):
        if os.path.basename(f) in SKIP:
            print(f"skipped  {f}")
            continue
        try:
            out, n, renamed = convert(f)
            print(f"{n:>8} rows  {out}" + (f"  ({renamed} names shortened)" if renamed else ""))
        except Exception as e:
            print(f"FAILED {f}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
