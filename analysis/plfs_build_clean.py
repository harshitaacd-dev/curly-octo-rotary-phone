"""Step 0: build one clean PLFS person file, July 2017 - June 2024, with AI exposure attached.

Reads the seven annual first-visit person files (the ones listed in detected_columns.csv),
keeps the variables the analysis needs, gives them the same names in every year, attaches
the ILO generative-AI exposure score of each worker's occupation, and stacks the years.

Put this file in the "PLFS Data" folder, next to:
    detected_columns.csv                 (made by plfs_counts_v3.py)
    nco2004_ai_exposure_3digit.csv       (exposure for 2017-18 to 2020-21, NCO-2004 codes)
    nco2015_ai_exposure_3digit.csv       (exposure for 2021-22 to 2023-24, NCO-2015 codes)
then run:

    python3 plfs_build_clean.py > build_output.txt

Outputs (next to this file):
    plfs_clean_2017_2024.dta   the clean data, one row per person. Individual records:
                               keep it on your computer, do not share it.
    build_output.txt           the variables found and the checks. Safe to share.

Check build_output.txt before using the data: the "variables used" list for each round,
then the four checks at the end. If a variable was not found or looks wrong, set it in
OVERRIDES below and run again.
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent

# Round folder -> first year of the round, and occupation code version.
ROUNDS = {
    "July17:Jun18": (2017, 2004),
    "July18:June19": (2018, 2004),
    "July19:June20": (2019, 2004),
    "July2020:June2021": (2020, 2004),
    "July21:June22": (2021, 2015),
    "July22:June23": (2022, 2015),
    "July23:June24": (2023, 2015),
}

# Example: OVERRIDES = {"July17:Jun18": {"quarter": "Quarter_per_fv"}}
OVERRIDES = {}

# Variables found by their Stata label (name patterns as a fallback). sex, age, nco, nic and
# weight come from detected_columns.csv, which was checked earlier.
#   role: (label pattern, name pattern, label words that rule a variable out, required?)
FIND = {
    "quarter":  (r"^quarter",                    r"^(qtr|quarter)",          r"",                     True),
    "sector":   (r"^sector",                     r"^(sector|b1q3)(_|$)",     r"",                     True),
    "state":    (r"^state",                      r"^(state|st)(_|$)",        r"region|stratum|sub",   True),
    "district": (r"^district",                   r"^(district|dist)(_|$)",   r"",                     False),
    "nss":      (r"^nss$|no\.? of sub.?samples surveyed", r"^nss(_|$)",     r"region",               False),
    "nsc":      (r"^nsc$|no\.? of sub.?samples (in|for) (the )?(stratum|strata)", r"^nsc(_|$)", r"", False),
    "marital":  (r"marital",                     r"^b4q7(_|$)",              r"",                     False),
    "edu":      (r"general\s*educ",              r"^b4q8(_|$)",              r"",                     True),
    "status":   (r"status code",                 r"^b5pt1q3(_|$)",           r"subsid|weekly|cws|daily|activity", True),
    "social":   (r"social\s*group",              r"^b3q[0-9]+_?.*soc",        r"",                     False),
    "religion": (r"religion",                    r"^b3q[0-9]+_?.*rel",        r"",                     False),
}
FROM_DETECTED = ["sex", "age", "nco", "nic", "weight"]


def labels_of(path):
    with pd.io.stata.StataReader(path) as r:
        return r.variable_labels()


def find(role, labels):
    lab_pat, name_pat, not_pat, _ = FIND[role]
    def ok(v):
        lab = (labels.get(v) or "").strip()
        return not (not_pat and re.search(not_pat, lab, re.I))
    by_label = [v for v, lab in labels.items() if re.search(lab_pat, (lab or "").strip(), re.I) and ok(v)]
    if role == "status":  # prefer the usual principal status (block 5 part 1) over other status codes
        by_label.sort(key=lambda v: (not re.search(r"b5pt1|pas$|principal", v + (labels[v] or ""), re.I), v))
    if by_label:
        return by_label[0]
    by_name = [v for v in labels if re.search(name_pat, v, re.I) and ok(v)]
    return by_name[0] if by_name else None


def plan_round(rnd, detected):
    row = detected[detected["round"] == rnd]
    if row.empty:
        sys.exit(f"{rnd} is not in detected_columns.csv: run plfs_counts_v3.py first.")
    row = row.iloc[0]
    path = BASE / row["file"]
    labels = labels_of(path)
    plan = {role: row[role] for role in FROM_DETECTED}
    for role in FIND:
        plan[role] = find(role, labels)
    plan.update(OVERRIDES.get(rnd, {}))
    missing = [r for r in FIND if FIND[r][3] and not plan.get(r)]
    print(f"\n{rnd}: {row['file']}")
    for role in FROM_DETECTED + list(FIND):
        v = plan.get(role)
        print(f"  {role:<9} {v or '-':<22} {labels.get(v, '') if v else '(not found)'}")
    if missing:
        hint = {r: [f"{v} [{l}]" for v, l in labels.items() if r[:4] in f"{v} {l}".lower()][:6] for r in missing}
        sys.exit(f"Required variable(s) not found in {rnd}: {missing}. Candidates: {hint}. "
                 "Set them in OVERRIDES and run again.")
    return path, plan


def digits(s, width):
    """Codes as zero-padded text: 41 -> '041', '4110' -> '411' (width 3)."""
    s = s.astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
    s = s.where(s.str.fullmatch(r"\d+"))
    return s.str.zfill(width).str[:width]


def num(s):
    return pd.to_numeric(s.astype(str).str.extract(r"(\d+)", expand=False), errors="coerce")


def load_round(rnd, first_year, version, detected, exposure):
    path, plan = plan_round(rnd, detected)
    cols = {v: k for k, v in plan.items() if v}
    df = pd.read_stata(path, columns=list(cols), convert_categoricals=False).rename(columns=cols)
    out = pd.DataFrame(index=df.index)
    out["round"] = f"{first_year}-{str(first_year + 1)[2:]}"
    out["nco_version"] = version

    # Quarter of the round (1 = Jul-Sep). Some rounds number quarters Q5-Q8 etc., so take it mod 4.
    q = num(df["quarter"])
    print(f"  quarter values: {sorted(q.dropna().unique().astype(int).tolist())}")
    qr = ((q - 1) % 4 + 1).astype("Int64")
    year = np.where(qr <= 2, first_year, first_year + 1)
    calq = np.where(qr <= 2, qr + 2, qr - 2)
    out["year"] = year
    out["qtr"] = calq
    out["quarter"] = pd.Series(year, index=df.index).astype(str) + "Q" + pd.Series(calq, index=df.index).astype(str)
    out["t"] = (out["year"] - 2017) * 4 + out["qtr"] - 3  # 2017Q3 = 0, ..., 2024Q2 = 27

    out["state"] = num(df["state"])
    if "district" in df:
        out["district"] = num(df["district"])
    out["urban"] = (num(df["sector"]) == 2).astype("int8")
    out["sex"] = num(df["sex"])
    out["female"] = (out["sex"] == 2).astype("int8")
    out["age"] = num(df["age"])
    for v in ("marital", "social", "religion"):
        if v in df:
            out[v] = num(df[v])
    out["edu"] = num(df["edu"])
    out["graduate"] = (out["edu"] >= 12).astype("int8")  # 12 graduate, 13 postgraduate and above
    out["status"] = num(df["status"])
    out["employed"] = out["status"].between(11, 51).astype("int8")
    out["unemployed"] = (out["status"] == 81).astype("int8")
    out["in_lf"] = (out["employed"] | out["unemployed"]).astype("int8")
    out["nco3"] = digits(df["nco"], 3).where(out["employed"] == 1)
    out["nic5"] = digits(df["nic"], 5).where(out["employed"] == 1)

    # Weight: MoSPI's rule for annual estimates from the first-visit file is MULT/100 where
    # the number of sub-samples surveyed (NSS) equals the number in the stratum (NSC), else
    # MULT/200. Check this against the README of each round.
    mult = pd.to_numeric(df["weight"], errors="coerce")
    if "nss" in df and "nsc" in df:
        out["weight"] = np.where(num(df["nss"]) == num(df["nsc"]), mult / 100, mult / 200)
        print("  weight: MULT/100 where NSS = NSC, else MULT/200")
    else:
        out["weight"] = mult / 100
        print("  weight: MULT/100 (NSS/NSC not found; check the round's README)")

    exp = exposure[version]
    out = out.merge(exp, left_on="nco3", right_index=True, how="left")
    out["age_group"] = pd.cut(out["age"], [14, 24, 34, 64], labels=["15-24", "25-34", "35-64"]).astype(str)
    out.loc[~out["age"].between(15, 64), "age_group"] = ""
    out["post"] = (out["t"] >= 22).astype("int8")  # 2023Q1 onwards (ChatGPT launched 30 Nov 2022)
    out["covid"] = out["t"].between(11, 15).astype("int8")  # 2020Q2 - 2021Q2
    print(f"  people: {len(out):,}")
    print("  education codes:", out["edu"].value_counts().sort_index().astype(int).to_dict())
    print("  status codes:", out["status"].value_counts().sort_index().astype(int).to_dict())
    return out


def exposure_files():
    e04 = pd.read_csv(BASE / "nco2004_ai_exposure_3digit.csv", dtype={"nco2004_3d": str}).set_index("nco2004_3d")
    e15 = pd.read_csv(BASE / "nco2015_ai_exposure_3digit.csv", dtype={"nco2015_3d": str}).set_index("nco2015_3d")
    keep04 = e04.rename(columns={"ilo_score_uw": "exp_ilo", "ilo_high_grad_share": "exp_ilo_high",
                                 "ilo_score_isco": "exp_ilo_alt"})[["exp_ilo", "exp_ilo_high", "exp_ilo_alt"]]
    keep15 = e15.rename(columns={"ilo_score_uw": "exp_ilo", "ilo_high_grad_share": "exp_ilo_high",
                                 "z_AIOE_w": "exp_aioe_z"})[["exp_ilo", "exp_ilo_high", "exp_aioe_z"]]
    keep15["exp_ilo_alt"] = keep15["exp_ilo"]  # the alternative route only differs for NCO-2004
    return {2004: keep04, 2015: keep15}


def wmean(x, w):
    m = x.notna() & w.notna()
    return np.average(x[m], weights=w[m]) if m.any() else np.nan


def checks(df):
    print("\n================ CHECKS ================")
    print("\n1. People per round (expect about 400,000-430,000):")
    print(df.groupby("round").size().to_string())

    print("\n2. Labour force participation, ages 15+, usual principal status, weighted (%):")
    a = df[df["age"] >= 15]
    lfpr = a.groupby(["round", "female"]).apply(lambda g: 100 * wmean(g["in_lf"], g["weight"])).unstack()
    lfpr.columns = ["men", "women"]
    print(lfpr.round(1).to_string())
    print("   Compare the trend with the PLFS annual reports (theirs also count subsidiary work, so are higher).")

    print("\n3. Exposure coverage among workers aged 15-64 (share of weighted workers with a score):")
    w = df[(df["employed"] == 1) & df["age"].between(15, 64)]
    cov = w.groupby("round").apply(lambda g: 100 * g.loc[g["exp_ilo"].notna(), "weight"].sum() / g["weight"].sum())
    print(cov.round(1).to_string())
    miss = w[w["exp_ilo"].isna()].groupby(["round", "nco3"], dropna=False).size().sort_values(ascending=False)
    if len(miss):
        print("   Most common job codes without a score (round, code, people):")
        print(miss.head(15).to_string())

    print("\n4. Seam check: average exposure of workers 15-64 by quarter (look for a jump 2021Q2 -> 2021Q3):")
    seam = w.groupby(["quarter", "female"]).apply(lambda g: wmean(g["exp_ilo"], g["weight"])).unstack()
    seam.columns = ["men", "women"]
    print(seam.round(3).to_string())


def main():
    detected = pd.read_csv(BASE / "detected_columns.csv")
    exposure = exposure_files()
    parts = []
    for rnd, (first_year, version) in ROUNDS.items():
        print(f"reading {rnd} ...", file=sys.stderr)
        parts.append(load_round(rnd, first_year, version, detected, exposure))
    df = pd.concat(parts, ignore_index=True)

    # One ruler for all years: standardise with the 2017-18 workforce (15-64, weighted).
    base = df[(df["round"] == "2017-18") & (df["employed"] == 1) & df["age"].between(15, 64)]
    mu = wmean(base["exp_ilo"], base["weight"])
    sd = np.sqrt(wmean((base["exp_ilo"] - mu) ** 2, base["weight"]))
    df["exposure_z"] = (df["exp_ilo"] - mu) / sd
    df["exposure_alt_z"] = (df["exp_ilo_alt"] - mu) / sd
    print(f"\nexposure_z = (ILO score - {mu:.4f}) / {sd:.4f}  (2017-18 workers aged 15-64, weighted)")

    checks(df)

    for c in ("nco3", "nic5", "age_group", "quarter", "round"):
        df[c] = df[c].fillna("").astype(str)
    df.to_stata(BASE / "plfs_clean_2017_2024.dta", write_index=False, version=118, variable_labels={
        "t": "Quarter index, 2017Q3 = 0", "post": "1 from 2023Q1 (after ChatGPT)",
        "covid": "1 for 2020Q2-2021Q2", "nco_version": "Occupation codes: 2004 or 2015",
        "nco3": "Occupation, 3-digit (version in nco_version)", "nic5": "Industry, NIC-2008 5-digit",
        "employed": "Usual principal status 11-51", "unemployed": "Usual principal status 81",
        "in_lf": "In labour force (principal status)", "graduate": "Education code 12 or 13",
        "weight": "Annual weight (MULT/100 or /200)", "exp_ilo": "ILO GenAI exposure score (0-1)",
        "exp_ilo_high": "Share of jobs in ILO gradients 3-4", "exp_ilo_alt": "ILO score via ISCO route",
        "exp_aioe_z": "Felten AIOE (2021-22 on only)", "exposure_z": "ILO score, standardised (2017-18 workers)",
        "exposure_alt_z": "ISCO-route score, standardised"})
    print(f"\nSaved plfs_clean_2017_2024.dta: {len(df):,} people, {df.shape[1]} variables. "
          "Keep it on your computer. Share build_output.txt only.")


if __name__ == "__main__":
    main()
