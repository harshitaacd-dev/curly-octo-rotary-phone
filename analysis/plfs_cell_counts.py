"""Day-1 feasibility check: how many women does PLFS record in data work?

Counts persons aged 15-64 by sex in
  - occupation NCO-2015 3-digit 413 ("keyboard operators": typists, data entry)
  - industry NIC-2008 6311x (data processing, hosting and related activities)
  - NIC 62 (IT services) and NIC 63 + 82 (wider definition)
for every PLFS round folder, unweighted and (approximately) weighted.

Put this file in the "PLFS Data" folder, next to the round folders
(2021, 2022, ..., July17/Jun18, ...). Each round folder holds CSV, Stata (.dta)
or JSON files; the script reads the person-level first-visit file in CSV or
Stata form and ignores JSON.

Step 1 (check what it found):   python3 plfs_cell_counts.py --inspect
Step 2 (count):                 python3 plfs_cell_counts.py

Outputs, written next to this file:
  detected_columns.csv  which file and which columns were used per round
  cell_counts.csv       the counts (share this one; it has no individual data)

If --inspect picks a wrong file or column for a round, set it in OVERRIDES
below and run again.
"""

import re
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent

# Example: OVERRIDES = {"July17/Jun18": {"file": "July17/Jun18/per_fv.dta", "nco": "b5pt1q6"}}
# Keys: file, sex, age, nco, nic, weight. Leave empty unless --inspect got something wrong.
OVERRIDES = {}

# Round folders to leave out. "2021" holds only current-weekly-status (CWS) job codes,
# not the usual principal activity used for every other round, so it is not comparable.
SKIP = {"2021"}

ROLES = ["sex", "age", "nco", "nic", "weight"]
PATTERNS = {
    "sex": re.compile(r"\bsex\b|gender", re.I),
    "age": re.compile(r"(^|[^a-z])age([^a-z]|$)", re.I),
    "nco": re.compile(r"nco|occupation", re.I),
    "nic": re.compile(r"\bnic\b|nic_|nic\d|industry", re.I),
    "weight": re.compile(r"mult|weight|wgt|mlt", re.I),
}
PREFER = re.compile(r"principal|usual|ups|\bps\b|_ps", re.I)
AVOID = re.compile(r"subsid|\bss\b|_ss|weekly|cws|daily|cds|day\d|_d\d|activity_?\d", re.I)
FIRST_VISIT = re.compile(r"fv|v1|first|perv1", re.I)
REVISIT = re.compile(r"(^|[^a-z])rv|perrv|hhrv|revisit|v[234](\b|_)", re.I)
HOUSEHOLD = re.compile(r"hh|household", re.I)


def columns_and_labels(path):
    """Return {column: label} without loading the data."""
    if path.suffix.lower() == ".dta":
        with pd.io.stata.StataReader(path) as r:
            labels = r.variable_labels()
        return {c: labels.get(c, "") for c in labels}
    head = pd.read_csv(path, nrows=0, low_memory=False)
    return {c: "" for c in head.columns}


# MoSPI's own variable codes win over label guesses: block 4 = demographics,
# block 5 part 1 = usual principal activity (q5 industry NIC, q6 occupation NCO).
CODES = {
    "sex": re.compile(r"^b4q5(_|$)", re.I),
    "age": re.compile(r"^b4q6(_|$)", re.I),
    "nic": re.compile(r"^b5pt1q5(_|$)", re.I),
    "nco": re.compile(r"^b5pt1q6(_|$)", re.I),
    "weight": re.compile(r"^(mult|mlt)", re.I),
}


def pick_column(role, cols):
    coded = [c for c in cols if CODES[role].search(c)]
    if coded:
        return coded[0]
    hits = [c for c, lab in cols.items() if PATTERNS[role].search(f"{c} {lab}")]
    if role == "age":
        hits = [c for c in hits if not re.search(r"wage|stage|percent|age_?group", f"{c} {cols[c]}", re.I)]
    if not hits:
        return None
    def score(c):
        text = f"{c} {cols[c]}"
        return (bool(PREFER.search(text)) - bool(AVOID.search(text)), -len(c))
    return sorted(hits, key=score, reverse=True)[0]


def person_files(round_dir, why):
    """Person-level, first-visit CSV/Stata files in a round folder (one format per file stem).

    Appends a one-line reason for every skipped file to `why`.
    """
    found = {}
    for p in sorted(round_dir.rglob("*")):
        if p.is_dir() or p.name.startswith("."):
            continue
        rel = p.relative_to(BASE)
        if p.suffix.lower() not in (".csv", ".dta"):
            why.append(f"  {rel}: skipped (not CSV or Stata)")
            continue
        name = p.stem
        if HOUSEHOLD.search(name) and not re.search(r"per", name, re.I):
            why.append(f"  {rel}: skipped (name looks like a household file)")
            continue
        if REVISIT.search(name) and not FIRST_VISIT.search(name):
            why.append(f"  {rel}: skipped (name looks like a revisit file)")
            continue
        try:
            cols = columns_and_labels(p)
        except Exception as e:  # unreadable file: report and move on
            why.append(f"  {rel}: could not read ({e})")
            continue
        missing = [r for r in ("sex", "age") if not pick_column(r, cols)]
        if not (pick_column("nco", cols) or pick_column("nic", cols)):
            missing.append("occupation/industry")
        if missing:
            sample = ", ".join(f"{c}" + (f" [{cols[c][:40]}]" if cols[c] else "") for c in list(cols)[:25])
            why.append(f"  {rel}: no {', '.join(missing)} column found. First columns: {sample}")
            continue
        # prefer .dta over .csv when both exist for the same stem
        key = name.lower()
        if key not in found or p.suffix.lower() == ".dta":
            found[key] = (p, cols)
    return list(found.values())


def detect(round_name, round_dir):
    ov = OVERRIDES.get(round_name, {})
    why = []
    if "file" in ov:
        p = BASE / ov["file"]
        files = [(p, columns_and_labels(p))]
    else:
        files = person_files(round_dir, why)
    if not files:
        print(f"{round_name}: no person-level CSV/Stata file with sex, age and occupation/industry found")
        print("\n".join(why) if why else "  (folder is empty)")
    if len(files) > 1:
        print(f"{round_name}: WARNING, {len(files)} person files found and all will be added up; "
              "if they are the same data in two formats, keep one:")
        print("\n".join(f"  {p.relative_to(BASE)}" for p, _ in files))
    plans = []
    for p, cols in files:
        plan = {"round": round_name, "file": str(p.relative_to(BASE))}
        for role in ROLES:
            plan[role] = ov.get(role) or pick_column(role, cols)
            plan[f"{role}_label"] = cols.get(plan[role], "") if plan[role] else ""
        plans.append(plan)
    return plans


def load(plan):
    use = [plan[r] for r in ROLES if plan[r]]
    path = BASE / plan["file"]
    if path.suffix.lower() == ".dta":
        df = pd.read_stata(path, columns=use, convert_categoricals=False)
    else:
        df = pd.read_csv(path, usecols=use, dtype=str, low_memory=False)
    return df.rename(columns={plan[r]: r for r in ROLES if plan[r]})


def code(series, width):
    """Turn 413, 413.0, '0413 ', '01111' into zero-padded strings."""
    s = series.astype(str).str.strip().str.replace(r"\.0+$", "", regex=True)
    return s.where(~s.str.fullmatch(r"\d+"), s.str.zfill(width))


def sex_code(series):
    s = series.astype(str).str.strip().str.lower().str.replace(r"\.0+$", "", regex=True)
    return s.replace({"male": "1", "m": "1", "female": "2", "f": "2"})


def count(df):
    df = df.copy()
    df["sex"] = sex_code(df["sex"])
    w_all = pd.to_numeric(df["weight"], errors="coerce") / 100 if "weight" in df else None
    rows = [{"cell": "All persons in file (any age)", "sex": label,
             "n_unweighted": int((df["sex"] == c).sum()),
             "n_weighted_approx": round(w_all[df["sex"] == c].sum()) if w_all is not None else None}
            for c, label in (("1", "men"), ("2", "women"))]
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df[(df["age"] >= 15) & (df["age"] <= 64)]
    w = pd.to_numeric(df["weight"], errors="coerce") / 100 if "weight" in df else None
    nco = code(df["nco"], 3) if "nco" in df else pd.Series("", index=df.index)
    nic = code(df["nic"], 5) if "nic" in df else pd.Series("", index=df.index)
    cells = {
        "Aged 15-64": pd.Series(True, index=df.index),
        "Aged 15-64 with an occupation code": nco.str.fullmatch(r"\d{3}"),
        "NCO 413 keyboard operators": nco.str.startswith("413"),
        "NIC 6311 data processing": nic.str.startswith("6311"),
        "NIC 62 IT services": nic.str.startswith("62"),
        "NIC 63 + 82 (wide definition)": nic.str.match(r"^(63|82)"),
    }
    for cell, mask in cells.items():
        for c, label in (("1", "men"), ("2", "women")):
            m = mask & (df["sex"] == c)
            rows.append({"cell": cell, "sex": label, "n_unweighted": int(m.sum()),
                         "n_weighted_approx": round(w[m].sum()) if w is not None else None})
    return rows


def main():
    inspect = "--inspect" in sys.argv
    rounds = sorted(d for d in BASE.iterdir() if d.is_dir() and not d.name.startswith("."))
    plans = []
    for d in rounds:
        if d.name in SKIP:
            print(f"{d.name}: skipped (listed in SKIP)")
            continue
        plans.extend(detect(d.name, d))
    detected = pd.DataFrame(plans)
    detected.to_csv(BASE / "detected_columns.csv", index=False)
    if detected.empty:
        sys.exit("Nothing to count.")
    print(detected[["round", "file"] + ROLES].to_string(index=False))
    if inspect:
        print("\nLabels of the occupation and industry columns used (should say principal/usual activity):")
        for _, r in detected.iterrows():
            print(f"  {r['round']}: nco={r['nco']} [{r['nco_label']}] | nic={r['nic']} [{r['nic_label']}]")
    missing = detected[detected[["sex", "age"]].isna().any(axis=1) | detected[["nco", "nic"]].isna().all(axis=1)]
    if not missing.empty:
        print("\nCheck these rows: a needed column was not found. Set it in OVERRIDES.")
    if inspect:
        print("\nInspect only. If the files and columns look right, run without --inspect.")
        return

    out = []
    for plan in plans:
        print(f"counting {plan['file']} ...")
        for row in count(load(plan)):
            out.append({"round": plan["round"], "file": plan["file"], **row})
    table = pd.DataFrame(out).groupby(["round", "cell", "sex"], as_index=False)[
        ["n_unweighted", "n_weighted_approx"]].sum()
    table.to_csv(BASE / "cell_counts.csv", index=False)
    print()
    print(table.pivot_table(index=["cell", "sex"], columns="round",
                            values="n_unweighted", aggfunc="sum").to_string())
    thin = table[(table["sex"] == "women") & (table["n_unweighted"] < 100)]
    if not thin.empty:
        print("\nCells with fewer than 100 women (pool rounds or widen the definition):")
        print(thin[["round", "cell", "n_unweighted"]].to_string(index=False))
    print("\nSaved cell_counts.csv and detected_columns.csv. Share both; neither has individual data.")


if __name__ == "__main__":
    main()
