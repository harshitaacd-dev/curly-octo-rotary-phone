"""Police capacity by State from BPR&D, Data on Police Organizations (as on 1 January of each year).

Usage: python scripts/police_capacity.py
    writes data/analysis/state_police.csv       (one row per State; 2024 report + 2020 civil police)
    and    data/analysis/state_police_year.csv  (State x year 2020-2024: cyber police stations and cells)
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
    return 0.0 if v == "-" else (float("nan") if v in ("NA", "NP", "N/A", "@") else float(v.replace(",", "")))


# Yearly cyber capacity. Each report: (file, anchor of cyber-station table, column index, anchor of cyber-cell table).
# Text conversions of the BPR&D reports for 1 January 2020, 2021, 2022 and 2024 (2023 not available).
YEARS = {
    2020: ("data/external/controls/bprd_dopo_2020.md", r"^CYBER CRIME POLICE$", 1),
    2021: ("data/external/controls/bprd_dopo_2021.md", r"^CYBER CRIME$", 6),
    2022: ("data/external/controls/bprd_dopo_2022.md", r"^CYBER$", 6),
    2024: ("data/external/controls/bprd_dopo_2024.md", r"^CYBER$", 6),
}
# Uttar Pradesh reports cyber cells as "@" with a footnote: 75 district cyber cells (2021),
# 75 district cells + 4 in commissionerates (2022).
UP_CELLS = {2021: 75.0, 2022: 79.0}


def rows_after(lines, anchor):
    """'<n> <State> v1 v2 ...' rows of the table that follows the first line matching `anchor`."""
    i = next(k for k, l in enumerate(lines) if re.search(anchor, l.strip()))
    rows, buf = [], ""
    for l in lines[i + 1:]:
        l = l.strip()
        if re.match(r"^(All India|TOTAL) [\d,]", l):
            break
        if re.match(r"^\d+ [A-Z]", l):
            buf = l
        elif buf:
            buf = buf + " " + l
        else:
            continue
        m = re.match(r"^\d+ ([A-Za-z&\. ]+?) \*? ?((?:[\d,\.]+|-|NA|NP|N/A|@)(?: (?:[\d,\.]+|-|NA|NP|N/A|@))*)$", buf)
        if m:
            rows.append((m.group(1).strip(), m.group(2).split()))
            buf = ""
    return rows


def unit(name):
    name = NAMES.get(name, name)
    if "Haveli" in name or "Daman" in name:
        return "D&N Haveli and Daman & Diu"
    return norm_state(name.replace("A & N", "A&N"))


def yearly():
    out = []
    for year, (path, anchor, col) in YEARS.items():
        lines = open(path, encoding="utf-8").read().splitlines()
        ce = {}
        for n, v in rows_after(lines, r"STATES/UTs NUMBER OF CYBER"):
            u = unit(n)
            val = UP_CELLS.get(year) if (u == "Uttar Pradesh" and v[0] == "@") else num(v[0])
            ce[u] = ce.get(u, 0) + val if u in ce else val
        st_sum = {}
        for n, v in rows_after(lines, anchor):
            if len(v) > col and not pd.isna(num(v[col])):  # "@" = included in another unit's row
                u = unit(n)
                st_sum[u] = st_sum.get(u, 0) + num(v[col])
        for u in sorted(set(st_sum) | set(ce)):
            out.append({"state": u, "year": year, "cyber_police_stations": st_sum.get(u), "cyber_cells": ce.get(u)})
    d = pd.DataFrame(out)
    d = d.groupby(["state", "year"], as_index=False).sum(min_count=1)
    # 2023 report not available: average of 2022 and 2024
    mid = d[d.year.isin([2022, 2024])].groupby("state", as_index=False)[["cyber_police_stations", "cyber_cells"]].mean()
    mid["year"], mid["interpolated"] = 2023, 1
    d["interpolated"] = 0
    d = pd.concat([d, mid], ignore_index=True).sort_values(["state", "year"])
    d["cyber_units"] = d.cyber_police_stations + d.cyber_cells
    return d


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
    y = yearly()
    y.to_csv(OUT.replace(".csv", "_year.csv"), index=False)
    print(y.pivot(index="state", columns="year", values="cyber_units").to_string())
    print(y.groupby("year")[["cyber_police_stations", "cyber_cells"]].sum())


if __name__ == "__main__":
    main()
