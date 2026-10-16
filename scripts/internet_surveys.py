"""Internet use by State/UT, age and gender from official household surveys.

Usage: python scripts/internet_surveys.py data/external/surveys data/clean/internet_use_surveys_long.csv

Reads the page extracts in data/external/surveys/ (see its README) and writes one long file:
    survey, period, indicator, state, age_group, gender, sector, value_pct, source_file, source_table

  NSS 75th round (2017-18)  Report 585, Statements 7.5.1 / 7.6.1 (State x gender x sector, age 5+)
                            and Table 18 (all-India x age x gender x sector)
  NFHS-5 (2019-21)          Table 3.7 (State x gender, age 15-49) and Table 3.6 (age x gender)
  CAMS, NSS 79th (2022-23)  Report 590, Tables 16 / 17 (State x age 15-24 / 15-29 / 15+ x gender x sector)
  CMS: Telecom (Jan-Mar 2025) press note, all-India only, typed in below

The surveys define internet use differently (see the README); compare levels only within a survey.
"""
import csv, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(__file__))
from internet_trai import STATE_NAME  # noqa: E402

TOKEN = re.compile(r"^(-|\d[\d,]*\.?\d*)$")
SECTORS = ["Rural", "Urban", "Total"]
GENDERS = ["Male", "Female", "Total"]
USED_3M = "used internet in last 3 months"
ABLE = "able to use internet"
# CMS: Telecom 2025 press note (29 May 2025), page 5 table and Fig. 3. All-India only.
CMS_2025 = [  # (age, sector, gender, value)
    ("15-24", "Rural", "Male", 95.7), ("15-24", "Rural", "Female", 91.1),
    ("15-24", "Urban", "Male", 97.0), ("15-24", "Urban", "Female", 95.0),
    ("15-29", "Rural", "Male", 95.4), ("15-29", "Rural", "Female", 89.8),
    ("15-29", "Urban", "Male", 96.9), ("15-29", "Urban", "Female", 94.3),
    ("15-29", "Rural", "Total", 92.7), ("15-29", "Urban", "Total", 95.7), ("15-29", "Total", "Total", 94.3),
    ("15+", "Rural", "Male", 72.1), ("15+", "Rural", "Female", 57.6),
    ("15+", "Urban", "Male", 85.5), ("15+", "Urban", "Female", 74.0),
]


def lines_of(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout.splitlines()


def split_values(line):
    parts = line.split()
    k = len(parts)
    while k and TOKEN.match(parts[k - 1]):
        k -= 1
    return " ".join(parts[:k]), parts[k:]


def num(s):
    return None if s == "-" else float(s.replace(",", ""))


def state_of(*candidates):
    for label in candidates:
        if re.search(r"all-India|^\s*India\s*$", label, re.I):
            return "All India"
        for rx, s in STATE_NAME:
            if s != "All India" and re.search(rx, label, re.I):
                return s
    return None


def nine_col_tables(lines, title_rx, indicator_of, age_of):
    """Tables of State x (rural, urban, all) x (male, female, person)."""
    out, indicator, age, pending = [], None, None, []
    for l in lines:
        if re.search(title_rx, l):
            indicator, age, pending = indicator_of(l), age_of(l), []
            continue
        m = re.search(r"Age:\s*(.+?)\s*years?(?: and above)?\s*$", l)
        if m:
            age = "15+" if "above" in l else m.group(1).replace(" ", "")
            continue
        name, values = split_values(l)
        if indicator and len(values) in (9, 6) and (name or pending):
            state = state_of(name, " ".join(pending + [name])) if name else state_of(" ".join(pending))
            if state is None:
                raise ValueError(f"unknown State/UT: {name!r} / {pending}")
            if len(values) == 6:  # rural not published (Delhi in NSS 75th)
                values = [None] * 3 + values
            for i, v in enumerate(values):
                if v is not None:
                    out.append((indicator, state, age, GENDERS[i % 3], SECTORS[i // 3], num(v)))
            pending = []
        elif re.search(r"[A-Za-z]", l):
            pending = (pending + [name or l.strip()])[-2:]
    return out


def nss75(path):
    lines = lines_of(path)
    t18 = next(i for i, l in enumerate(lines) if re.search(r"^\s*Table \(18\)", l))
    rows = nine_col_tables(
        lines[:t18], r"Statement 7\.[56]\.1:",
        lambda l: "used internet in last 30 days" if "7.6.1" in l else ABLE, lambda l: "5+")
    sector = gender = None
    for l in lines[t18:]:  # Table 18: all-India by age group
        m = re.search(r"Sector:\s*(Rural\s*\+\s*Urban|Rural|Urban).*Gender:\s*(Male|Female|Persons)", l)
        if m:
            sector = "Total" if "+" in m.group(1) else m.group(1)
            gender = {"Persons": "Total"}.get(m.group(2), m.group(2))
            continue
        name, values = split_values(l)
        if sector and len(values) == 9 and re.match(r"^(\d+-\d+|\d+ & above)$", name):
            age = name.replace(" & above", "+")
            if age == "5+":  # same figures as the State statements' all-India row
                continue
            rows.append((ABLE, "All India", age, gender, sector, num(values[3])))
            rows.append(("used internet in last 30 days", "All India", age, gender, sector, num(values[6])))
    return rows


def nfhs5(path):
    lines, rows, section, pending = lines_of(path), [], None, []
    ind = "ever used internet"
    for l in lines:
        if re.search(r"Table 3\.7", l):
            section = "state"
        elif re.search(r"Table 3\.6", l):
            section = "background"
        name, values = split_values(l)
        if section == "background" and len(values) == 4:
            label = name.strip()
            if re.match(r"^\d+-\d+$", label):
                key = ("15-49", label, "Total")
            elif label in ("Urban", "Rural"):
                key = (label, "15-49", label)
            else:  # "Total age 15-49" repeats Table 3.7's India row
                continue
            sector, age = (key[2], key[1]) if label in ("Urban", "Rural") else ("Total", key[1])
            rows.append((ind, "All India", age, "Female", sector, num(values[0])))
            rows.append((ind, "All India", age, "Male", sector, num(values[2])))
        elif section == "state" and len(values) == 12:
            state = state_of(name) or state_of(" ".join(pending + [name]))
            if state is None:
                raise ValueError(f"unknown State/UT: {name!r}")
            rows.append((ind, state, "15-49", "Female", "Total", num(values[5])))
            rows.append((ind, state, "15-49", "Male", "Total", num(values[11])))
            pending = []
        elif re.search(r"[A-Za-z]", l):
            pending = (pending + [l.strip()])[-1:]
    return rows


def cams(path):
    return nine_col_tables(
        lines_of(path), r"^\s*Table 1[67]: Percentage of persons",
        lambda l: ABLE if "able to use" in l else USED_3M, lambda l: None)


def main(src, out):
    jobs = [
        ("NSS 75th round", "2017-18", "nss75_2017_18_internet_tables.pdf", nss75,
         "Report 585, Statements 7.5.1-7.6.1, Table 18"),
        ("NFHS-5", "2019-21", "nfhs5_2019_21_tables3_6_3_7.pdf", nfhs5, "India report, Tables 3.6-3.7"),
        ("CAMS (NSS 79th round)", "2022-23", "cams_2022_23_tables16_17.pdf", cams, "Report 590, Tables 16-17"),
    ]
    records = []
    for survey, period, fname, fn, table in jobs:
        rows = fn(os.path.join(src, fname))
        records += [(survey, period) + r + (fname, table) for r in rows]
        print(f"{survey}: {len(rows)} values", file=sys.stderr)
    for age, sector, gender, v in CMS_2025:
        records.append(("CMS: Telecom", "2025 (Jan-Mar)", USED_3M, "All India", age, gender, sector, v,
                        "cms_telecom_2025_press_note.pdf", "Press note 29 May 2025, p.4-5"))

    # Checks: no duplicate keys; every survey's State tables cover the expected States/UTs.
    keys = [r[:7] for r in records]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        raise ValueError(f"duplicate rows: {sorted(dup)[:5]}")
    for survey, n in (("CAMS (NSS 79th round)", 37), ("NFHS-5", 37), ("NSS 75th round", 23)):
        states = {r[3] for r in records if r[0] == survey}
        if len(states) != n:
            print(f"warning {survey}: {len(states)} States/UTs incl. All India, expected {n}", file=sys.stderr)

    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["survey", "period", "indicator", "state", "age_group", "gender", "sector",
                    "value_pct", "source_file", "source_table"])
        w.writerows(records)
    print(f"wrote {out}: {len(records)} rows", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
