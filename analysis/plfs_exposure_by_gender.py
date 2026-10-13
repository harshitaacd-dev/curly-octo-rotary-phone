"""Are Indian women more or less exposed to generative AI than men? (Table 1)

For each NCO-2015 PLFS round (July 2021 onwards), attaches the ILO generative-AI
exposure score (Gmyrek et al. 2025, WP 140) to each worker's 3-digit occupation,
using Mishra's NCO-2015 crosswalk (github.com/Kpmishra1998/nco2015-ai-exposure),
and reports, by sex: the share of workers in low / middle / high exposure jobs,
the share in ILO "high exposure" jobs, and the mean score. Weighted by mult.

Put this file and nco2015_ai_exposure_3digit.csv in the "PLFS Data" folder,
next to detected_columns.csv (made by plfs_counts_v3.py), then run:

    python3 plfs_exposure_by_gender.py > exposure_output.txt

Output: exposure_by_gender.csv (shares only, no individual data).

Definitions
  worker      aged 15-64 with a 3-digit occupation code (usual principal status)
  low/mid/high  thirds of all workers in 2021-22 (both sexes, weighted), ranked by
              ILO score; the same cut-offs are used for every round
  ILO high    at least half of the occupation's 4-digit ISCO jobs are in ILO
              exposure gradients 3-4 (the ILO's own "highest exposure" groups)
  graduate    general education code 12 (graduate) or 13 (postgraduate and above);
              the code counts are printed so this can be checked against the codebook
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
ROUNDS = ["July21:June22", "July22:June23", "July23:June24"]  # NCO-2015, annual files
CUT_ROUND = ROUNDS[0]
SCORE = "ilo_score_uw"

EDU = re.compile(r"general\s*educ", re.I)
SECTOR = re.compile(r"^sector$", re.I)


def find_extra(path):
    """Education and sector variables, found by their Stata labels."""
    with pd.io.stata.StataReader(path) as r:
        labels = r.variable_labels()
    edu = next((v for v, lab in labels.items() if EDU.search(lab or "")), None)
    sector = next((v for v, lab in labels.items() if SECTOR.search((lab or "").strip())
                   or v.lower().startswith("sector")), None)
    return edu, sector


def load(plan, exposure):
    path = BASE / plan["file"]
    edu, sector = find_extra(path)
    cols = {plan["sex"]: "sex", plan["age"]: "age", plan["nco"]: "nco", plan["weight"]: "w"}
    if edu:
        cols[edu] = "edu"
    if sector:
        cols[sector] = "sector"
    df = pd.read_stata(path, columns=list(cols), convert_categoricals=False).rename(columns=cols)
    print(f"{plan['round']}: {plan['file']} | education={edu} | sector={sector}")
    for c in ("sex", "age", "w", "edu", "sector"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    nco = df["nco"].astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
    df["nco"] = nco.where(~nco.str.fullmatch(r"\d+"), nco.str.zfill(3).str[:3])
    df = df[df["age"].between(15, 64) & df["nco"].str.fullmatch(r"\d{3}") & df["sex"].isin([1, 2])]
    df = df.merge(exposure, left_on="nco", right_on="nco2015_3d", how="left")
    matched = df[SCORE].notna()
    if "edu" in df:
        print("  education codes (workers):", df["edu"].value_counts().sort_index().to_dict())
    print(f"  workers 15-64: {len(df):,}; matched to an exposure score: "
          f"{df.loc[matched, 'w'].sum() / df['w'].sum():.1%} of weighted workers")
    unmatched = df.loc[~matched, "nco"].value_counts().head(8)
    if len(unmatched):
        print("  most common unmatched codes:", ", ".join(f"{k} ({v})" for k, v in unmatched.items()))
    return df[matched].copy()


def weighted_cutoffs(df):
    d = df.sort_values(SCORE)
    cum = d["w"].cumsum() / d["w"].sum()
    return [d.loc[cum >= q, SCORE].iloc[0] for q in (1 / 3, 2 / 3)]


def summarise(df, cuts):
    w = df["w"]
    # Ties at a cut-off go to the lower group, so thirds can be uneven where many
    # workers share one score (e.g. farmers).
    low = df[SCORE] <= cuts[0]
    high = df[SCORE] > cuts[1]
    mid = ~low & ~high
    return {
        "n_unweighted": len(df),
        "pct_low": 100 * w[low].sum() / w.sum(),
        "pct_middle": 100 * w[mid].sum() / w.sum(),
        "pct_high": 100 * w[high].sum() / w.sum(),
        "pct_ilo_high": 100 * w[df["ilo_high_grad_share"] >= 0.5].sum() / w.sum(),
        "mean_ilo_score": np.average(df[SCORE], weights=w),
    }


def groups(df):
    yield "All workers 15-64", df
    yield "Age 15-24", df[df["age"].between(15, 24)]
    yield "Age 25-34", df[df["age"].between(25, 34)]
    yield "Age 35-64", df[df["age"].between(35, 64)]
    yield "Outside farming (NCO not 6xx/921)", df[~df["nco"].str.match(r"^(6|921)")]
    if "sector" in df:
        yield "Rural", df[df["sector"] == 1]
        yield "Urban", df[df["sector"] == 2]
    if "edu" in df:
        yield "Graduates", df[df["edu"] >= 12]
        yield "Urban graduates", df[(df["edu"] >= 12) & (df.get("sector") == 2)]


def main():
    exposure = pd.read_csv(BASE / "nco2015_ai_exposure_3digit.csv", dtype={"nco2015_3d": str})
    exposure = exposure[["nco2015_3d", SCORE, "ilo_high_grad_share"]]
    plans = pd.read_csv(BASE / "detected_columns.csv")
    data = {r: load(plans[plans["round"] == r].iloc[0], exposure)
            for r in ROUNDS if (plans["round"] == r).any()}
    if CUT_ROUND not in data:
        raise SystemExit(f"{CUT_ROUND} not found in detected_columns.csv")
    cuts = weighted_cutoffs(data[CUT_ROUND])
    print(f"\nExposure thirds (ILO score, cut-offs from {CUT_ROUND}): "
          f"low <= {cuts[0]:.3f} < middle <= {cuts[1]:.3f} < high\n")

    rows = []
    for rnd, df in data.items():
        for name, g in groups(df):
            for code, sex in ((2, "women"), (1, "men")):
                sub = g[g["sex"] == code]
                if len(sub):
                    rows.append({"round": rnd, "group": name, "sex": sex, **summarise(sub, cuts)})
    table = pd.DataFrame(rows)
    table.to_csv(BASE / "exposure_by_gender.csv", index=False, float_format="%.2f")

    show = ["pct_low", "pct_middle", "pct_high", "pct_ilo_high", "mean_ilo_score", "n_unweighted"]
    with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
        for rnd in data:
            print(f"=== {rnd} (percent of workers in each group; weighted) ===")
            t = table[table["round"] == rnd].set_index(["group", "sex"])[show]
            print(t.to_string(), "\n")
    small = table[table["n_unweighted"] < 100]
    if not small.empty:
        print("Cells with fewer than 100 people (treat with care):")
        print(small[["round", "group", "sex", "n_unweighted"]].to_string(index=False))
    print("\nSaved exposure_by_gender.csv. Share it and exposure_output.txt; neither has individual data.")


if __name__ == "__main__":
    main()
