"""State control variables for Parts 1 and 2: income per head and urban share.

Usage: python scripts/build_controls.py   (writes data/analysis/state_controls.csv)

income: per capita net state domestic product at constant 2011-12 prices (rupees), RBI Handbook of
    Statistics on Indian States 2024-25, Table 20, saved from
    https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=23469 as
    data/external/controls/rbi_hsis_2024_25_table20_per_capita_nsdp_constant.html.
    nsdp_pc_2019 = 2019-20 (pre-period); nsdp_pc_avg = mean of 2017-18 to 2022-23.
    Merged units (J&K + Ladakh; DNH + Daman & Diu) take the value published for the unit RBI reports.
urban share: share of persons aged 15+ living in urban areas, implied by CAMS 2022-23
    (MoSPI Report 590): for each indicator, total = u x urban + (1 - u) x rural, so
    u = (total - rural) / (urban - rural). Averaged over 'used internet in last 3 months' and
    'able to use internet'. Census 2011 rural-urban tables could not be downloaded here; the implied
    shares are close to the Census 2011 figures for the States checked (e.g. Kerala, Bihar, Delhi,
    Maharashtra, Uttar Pradesh). Replace with Census figures if available.
"""
import os, re, sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from build_analysis_panels import norm_state  # noqa: E402

RBI = "data/external/controls/rbi_hsis_2024_25_table20_per_capita_nsdp_constant.html"
ACCESS = "data/external/internet_access/india_internet_access_by_state_age_gender.xlsx"
OUT = "data/analysis/state_controls.csv"


def rbi_income():
    t = open(RBI, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    x = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    part2 = x[x.find("(Concld.)"):]
    years = re.findall(r"20\d\d-\d\d", part2)[:8]
    body = part2[part2.find(years[-1]) + len(years[-1]):]
    rows = {}
    for m in re.finditer(r"([A-Z][A-Za-z&\. ]+?)\*? ((?:(?:[\d,]+|-) ){7}(?:[\d,]+|-))(?= [A-Z]|$| )", body):
        name, vals = m.group(1).strip(), m.group(2).split()
        if name in rows or len(vals) != 8:
            continue
        rows[name] = [float(v.replace(",", "")) if v != "-" else np.nan for v in vals]
    d = pd.DataFrame.from_dict(rows, orient="index", columns=years)
    d.index = [norm_state(s) for s in d.index]
    d = d.groupby(level=0).first()
    return pd.DataFrame({"nsdp_pc_2019": d["2019-20"], "nsdp_pc_avg": d[years[:6]].mean(axis=1)})


def urban_share():
    long = pd.read_excel(ACCESS, "Survey_Data_Long")
    c = long[long.survey.str.contains("CAMS") & (long.gender == "Total") & (long.age_group == "15+")]
    w = c.pivot_table(index=["state", "indicator"], columns="sector", values="value_pct").reset_index()
    w["u"] = (w.Total - w.Rural) / (w.Urban - w.Rural)
    u = w[w.Urban != w.Rural].groupby("state").u.mean().clip(0, 1) * 100
    u.index = [norm_state(s) for s in u.index]
    return u.groupby(level=0).mean().rename("urban_share_cams")


def main():
    acc = pd.read_csv("data/analysis/state_access.csv", index_col=0)
    out = pd.DataFrame(index=acc.index).join(rbi_income()).join(urban_share())
    out.round(2).to_csv(OUT, index_label="state")
    print(out.round(1).to_string())
    print("missing:", out.isna().sum().to_dict())


if __name__ == "__main__":
    main()
