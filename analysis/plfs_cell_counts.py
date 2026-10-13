"""Day-1 feasibility check: how many women does PLFS record in data work? (Stata files)

Counts persons by sex in each PLFS round:
  - all persons in the file, persons aged 15-64, and those with an occupation code
  - occupation NCO-2015 3-digit 413 ("keyboard operators": typists, data entry)
  - industry NIC-2008 6311x (data processing, hosting and related activities)
  - NIC 62 (IT services) and NIC 63 + 82 (wider definition)
unweighted and (approximately) weighted.

Put this file in the "PLFS Data" folder, next to the round folders
(2022, 2023, ..., July17:Jun18, ...). Each round folder may hold the Stata
files directly or inside a sub-folder; the script searches all of them.

Step 1 (check what it found):   python3 plfs_cell_counts.py --inspect
Step 2 (count):                 python3 plfs_cell_counts.py > counts_output.txt

Outputs, written next to this file (no individual data in either):
  detected_columns.csv  which file and which variables were used per round
  cell_counts.csv       the counts

If --inspect picks a wrong file or variable, set it in OVERRIDES and run again.
"""

import re
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent

# Example: OVERRIDES = {"2025": {"file": "2025/STATA/cperv12025.dta", "nco": "pas_nco"}}
# Keys: file (path relative to this folder), sex, age, nco, nic, weight.
OVERRIDES = {}

# Round folders to leave out. "2021" holds only current-weekly-status (CWS) job codes,
# not the usual principal activity used for every other round, so it is not comparable.
SKIP = {"2021"}

ROLES = ["sex", "age", "nco", "nic", "weight"]

# MoSPI variable codes win over label guesses: block 4 = demographics,
# block 5 part 1 = usual principal activity (q5 industry NIC, q6 occupation NCO).
CODES = {
    "sex": re.compile(r"^b4q5(_|$)", re.I),
    "age": re.compile(r"^b4q6(_|$)", re.I),
    "nic": re.compile(r"^b5pt1q5(_|$)", re.I),
    "nco": re.compile(r"^b5pt1q6(_|$)", re.I),
    "weight": re.compile(r"^(mult|mlt)", re.I),
}
# Fallback: match on the variable name plus its Stata label.
PATTERNS = {
    "sex": re.compile(r"\bsex\b|gender", re.I),
    "age": re.compile(r"(^|[^a-z])age([^a-z]|$)", re.I),
    "nco": re.compile(r"nco|occupation", re.I),
    "nic": re.compile(r"\bnic\b|nic_|nic\d|industry", re.I),
    "weight": re.compile(r"mult|weight|wgt|mlt", re.I),
}
NOT_AGE = re.compile(r"wage|stage|percent|age_?group", re.I)
PREFER = re.compile(r"principal|usual|ups|\bps\b|_ps|\bpas\b", re.I)
AVOID = re.compile(r"subsid|\bss\b|_ss|weekly|cws|daily|cds|day\d|_d\d|activity_?\d", re.I)

PERSON = re.compile(r"per", re.I)
FIRST_VISIT = re.compile(r"fv|v1|first", re.I)
REVISIT = re.compile(r"(^|[^a-z])rv|perrv|hhrv|revisit|v[234](\b|_)", re.I)


def variables(path):
    """{variable: label} of a Stata file, without loading the data."""
    with pd.io.stata.StataReader(path) as r:
        labels = r.variable_labels()
    return {v: labels.get(v, "") for v in labels}


def pick(role, cols):
    coded = [c for c in cols if CODES[role].search(c)]
    if coded:
        return coded[0]
    hits = [c for c, lab in cols.items() if PATTERNS[role].search(f"{c} {lab}")]
    if role == "age":
        hits = [c for c in hits if not NOT_AGE.search(f"{c} {cols[c]}")]
    if not hits:
        return None
    def score(c):
        text = f"{c} {cols[c]}"
        return (bool(PREFER.search(text)) - bool(AVOID.search(text)), -len(c))
    return max(hits, key=score)


def choose_file(round_dir, notes):
    """The one person-level, first-visit Stata file in a round folder.

    Every file looked at gets a one-line note explaining the decision.
    """
    candidates = []
    for p in sorted(round_dir.rglob("*")):
        if p.is_dir() or p.name.startswith("."):
            continue
        rel = p.relative_to(BASE)
        if p.suffix.lower() != ".dta":
            notes.append(f"  {rel}: ignored (not a Stata .dta file)")
            continue
        if REVISIT.search(p.stem) and not FIRST_VISIT.search(p.stem):
            notes.append(f"  {rel}: ignored (revisit file)")
            continue
        try:
            cols = variables(p)
        except Exception as e:
            notes.append(f"  {rel}: could not read ({e})")
            continue
        missing = [r for r in ("sex", "age") if not pick(r, cols)]
        if not (pick("nco", cols) or pick("nic", cols)):
            missing.append("occupation/industry")
        if missing:
            kind = "household-level file" if not PERSON.search(p.stem) else "file"
            sample = ", ".join(c + (f" [{cols[c][:35]}]" if cols[c] else "") for c in list(cols)[:20])
            notes.append(f"  {rel}: ignored ({kind}; no {', '.join(missing)} variable). First variables: {sample}")
            continue
        rank = (bool(PERSON.search(p.stem)), bool(FIRST_VISIT.search(p.stem)), p.stat().st_size)
        candidates.append((rank, p, cols))
    if not candidates:
        return None, None
    candidates.sort(key=lambda t: t[0], reverse=True)
    for _, p, _ in candidates[1:]:
        notes.append(f"  {p.relative_to(BASE)}: also usable, not used (another file ranked higher)")
    _, p, cols = candidates[0]
    return p, cols


def detect(round_name, round_dir):
    ov = OVERRIDES.get(round_name, {})
    notes = []
    if "file" in ov:
        p = BASE / ov["file"]
        cols = variables(p)
    else:
        p, cols = choose_file(round_dir, notes)
    if p is None:
        print(f"{round_name}: no person-level Stata file with sex, age and occupation/industry found")
        print("\n".join(notes) if notes else "  (no files in this folder)")
        return None
    if notes:
        print(f"{round_name}: using {p.relative_to(BASE)}")
        print("\n".join(notes))
    plan = {"round": round_name, "file": str(p.relative_to(BASE))}
    for role in ROLES:
        plan[role] = ov.get(role) or pick(role, cols)
        plan[f"{role}_label"] = cols.get(plan[role], "") if plan[role] else ""
    return plan


def load(plan):
    use = [plan[r] for r in ROLES if plan[r]]
    df = pd.read_stata(BASE / plan["file"], columns=use, convert_categoricals=False)
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
    df["w"] = pd.to_numeric(df["weight"], errors="coerce") / 100 if "weight" in df else float("nan")
    everyone = df
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df[(df["age"] >= 15) & (df["age"] <= 64)]
    nco = code(df["nco"], 3) if "nco" in df else pd.Series("", index=df.index)
    nic = code(df["nic"], 5) if "nic" in df else pd.Series("", index=df.index)
    groups = [
        ("All persons in file (any age)", everyone, pd.Series(True, index=everyone.index)),
        ("Aged 15-64", df, pd.Series(True, index=df.index)),
        ("Aged 15-64 with an occupation code", df, nco.str.fullmatch(r"\d{3}")),
        ("NCO 413 keyboard operators", df, nco.str.startswith("413")),
        ("NIC 6311 data processing", df, nic.str.startswith("6311")),
        ("NIC 62 IT services", df, nic.str.startswith("62")),
        ("NIC 63 + 82 (wide definition)", df, nic.str.match(r"^(63|82)")),
    ]
    rows = []
    for cell, frame, mask in groups:
        for c, label in (("1", "men"), ("2", "women")):
            m = mask & (frame["sex"] == c)
            rows.append({"cell": cell, "sex": label, "n_unweighted": int(m.sum()),
                         "n_weighted_approx": round(frame.loc[m, "w"].sum())})
    return rows


def main():
    inspect = "--inspect" in sys.argv
    plans = []
    for d in sorted(x for x in BASE.iterdir() if x.is_dir() and not x.name.startswith(".")):
        if d.name in SKIP:
            print(f"{d.name}: skipped (listed in SKIP)")
            continue
        plan = detect(d.name, d)
        if plan:
            plans.append(plan)
    if not plans:
        sys.exit("Nothing to count.")
    detected = pd.DataFrame(plans)
    detected.to_csv(BASE / "detected_columns.csv", index=False)
    print()
    print(detected[["round", "file"] + ROLES].to_string(index=False))
    print("\nLabels of the variables used (occupation and industry should be the principal/usual activity):")
    for _, r in detected.iterrows():
        print(f"  {r['round']}: sex={r['sex']} [{r['sex_label']}] | age={r['age']} [{r['age_label']}] | "
              f"nco={r['nco']} [{r['nco_label']}] | nic={r['nic']} [{r['nic_label']}] | "
              f"weight={r['weight']} [{r['weight_label']}]")
    if inspect:
        print("\nInspect only. If the files and variables look right, run without --inspect.")
        return

    out = []
    for plan in plans:
        print(f"counting {plan['file']} ...", file=sys.stderr)
        for row in count(load(plan)):
            out.append({"round": plan["round"], **row})
    table = pd.DataFrame(out)
    table.to_csv(BASE / "cell_counts.csv", index=False)
    print()
    print(table.pivot_table(index=["cell", "sex"], columns="round",
                            values="n_unweighted", aggfunc="sum", sort=False).to_string())
    small = table[(table["sex"] == "women") & (table["n_unweighted"] < 100)]
    if not small.empty:
        print("\nCells with fewer than 100 women (pool rounds or widen the definition):")
        print(small[["round", "cell", "n_unweighted"]].to_string(index=False))
    print("\nSaved cell_counts.csv and detected_columns.csv. Share both; neither has individual data.")


if __name__ == "__main__":
    main()
