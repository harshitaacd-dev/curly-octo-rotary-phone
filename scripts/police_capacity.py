"""Police capacity by State from BPR&D, Data on Police Organizations 2024 (as on 1 January 2024).

Usage: python scripts/police_capacity.py   (writes data/analysis/state_police.csv)
Input: data/external/controls/bprd_dopo_2024.md, a text conversion of
    https://bprd.mha.gov.in/uploads/pdf/Data%20on%20Police%20Organizations%20(2024)_%20(14-07-25)%20All.pdf
Tables used:
    Table 2.1.3 (continued)  actual strength of civil police          -> civil_police_actual
    Table 5.1.4              cyber crime police stations              -> cyber_police_stations
    Appendix 8               cyber cells                              -> cyber_cells
Per-population measures use NCRB 2023 population (data/analysis/state_year_panel.csv):
    civil_police_per_lakh, cyber_units_per_crore = (stations + cells) per crore people.
Pre-period general capacity: civil police per lakh in 2020 from the India Justice Report raw data
    (BPR&D figures; data/external/controls/ijr4_state_indicator_raw_data.xlsx) -> civil_police_per_lakh_2020.
"""
import os, re, sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from build_analysis_panels import norm_state  # noqa: E402

SRC = "data/external/controls/bprd_dopo_2024.md"
IJR = "data/external/controls/ijr4_state_indicator_raw_data.xlsx"
OUT = "data/analysis/state_police.csv"
NAMES = {"A & N Islands": "A&N Islands", "Jammu and Kashmir": "Jammu & Kashmir",
         "Dadra and Nagar Haveli and Daman and Diu": "D&N Haveli and Daman & Diu"}


def block(lines, start_pat, after=0):
    """Rows '<n> <State> v1 v2 ...' of the first table whose heading matches start_pat (skipping `after` matches)."""
    idx = [i for i, l in enumerate(lines) if re.search(start_pat, l)][after]
    rows, buf = [], ""
    for l in lines[idx + 1:]:
        if re.match(r"^(All India|TOTAL) [\d,]", l):
            break
        l = l.strip()
        if re.match(r"^\d+ [A-Z]", l) or (buf and not re.match(r"^\d+ [A-Z]", l)):
            buf = (buf + " " + l).strip() if buf and not re.match(r"^\d+ [A-Z]", l) else l
            m = re.match(r"^\d+ ([A-Za-z&\. ]+?) \*? ?((?:[\d,\.]+|-|NA|NP)(?: (?:[\d,\.]+|-|NA|NP))*)$", buf)
            if m:
                rows.append((m.group(1).strip(), m.group(2).split()))
                buf = ""
    return rows


def num(v):
    return 0.0 if v == "-" else (float("nan") if v in ("NA", "NP") else float(v.replace(",", "")))


def main():
    lines = open(SRC, encoding="utf-8").read().splitlines()
    out = {}
    for name, vals in block(lines, r"TABLE 2\.1\.3 -- \(CONTINUED"):
        out.setdefault(name, {})["civil_police_actual"] = num(vals[1])
    for name, vals in block(lines, r"TABLE 5\.1\.4 -- ACTUAL NUMBER OF SPECIAL PURPOSE"):
        out.setdefault(name, {})["cyber_police_stations"] = num(vals[6])
    for name, vals in block(lines, r"APPENDIX 8 -- NUMBER OF CYBER"):
        out.setdefault(name, {})["cyber_cells"] = num(vals[0])
    d = pd.DataFrame.from_dict(out, orient="index")
    d.index = [norm_state(NAMES.get(s, s)) for s in d.index]
    d = d.groupby(level=0).sum(min_count=1)
    pop = pd.read_csv("data/analysis/state_year_panel.csv").query("year == 2023").set_index("state").population_lakh
    d["civil_police_per_lakh"] = d.civil_police_actual / pop
    d["cyber_units"] = d.cyber_police_stations + d.cyber_cells
    d["cyber_units_per_crore"] = d.cyber_units / (pop / 100)
    ijr = pd.read_excel(IJR, "Police")
    ijr = ijr[ijr["Raw Data Name"].isin(["Total civil police", "Total population"])].copy()
    ijr["yr"] = ijr.Year.astype(str).str[:4]
    ijr = ijr[ijr.yr == "2020"].pivot_table(index="State", columns="Raw Data Name", values="Raw Data Value", aggfunc="first")
    ijr = ijr[~ijr.index.isin(["Dadra & Nagar Haveli", "Daman & Diu"])]
    ijr.index = [norm_state(s) for s in ijr.index]
    ijr = ijr.groupby(level=0).sum()
    d["civil_police_per_lakh_2020"] = ijr["Total civil police"] / (ijr["Total population"] * 10)
    d.round(2).to_csv(OUT, index_label="state")
    print(d.round(1).to_string())
    print("totals:", d[["civil_police_actual", "cyber_police_stations", "cyber_cells"]].sum().to_dict())


if __name__ == "__main__":
    main()
