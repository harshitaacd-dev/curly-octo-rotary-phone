"""Part 1 checks: is more internet access associated with more recorded cyber crime against women?

Usage: python scripts/access_checks.py   (writes analysis/models/access_checks.json)

Complements Model 1 (scripts/estimate_models.py), which asks whether cyber crime against women grew
faster in more-connected States and finds no relationship. Three simpler comparisons:

A  National trend, 2017-2024: log cases on log internet users (World Bank/ITU). Descriptive only:
   both series trend upwards.
B  Across States (levels), 2017-2024: cases ~ Access_s (standardised) | year, offset log population;
   Poisson, SE clustered by State. Offline crimes against women and cyber fraud as comparisons.
C  Within States over time, 2022-2024: cases ~ TRAI connections per 100 (per 10) | state + year,
   offset log population. Dec 2021 is excluded (TRAI misallocated several States).
   Delhi and Haryana are merged into one unit: TRAI's Delhi licence area includes Gurgaon and
   Faridabad (Haryana) and Noida and Ghaziabad (UP), and between 2023 and 2025 TRAI's State-wise count
   moved about 8 million subscriptions from Delhi to Haryana while the Delhi licence area grew
   (TRAI Performance Indicator Reports 2022-23 and Oct-Dec 2025; see analysis/models/README.md).
   Following Kumar and Somanathan (2009), the two are combined into a unit with consistent coverage.
   Checks: as reported (unmerged), drop Delhi, merge UP too, offline placebo, control for growth in
   other cyber crime (recording capacity), cyber versus offline in one model.
"""
import json, os, warnings

import numpy as np
import pandas as pd
import pyfixest as pf
from scipy.stats import pearsonr

warnings.filterwarnings("ignore")

PANEL = "data/analysis/state_year_panel.csv"
ACCESS = "data/external/internet_access/india_internet_access_by_state_age_gender.xlsx"
OUT = "analysis/models/access_checks.json"
SUMS = ["cyber_vaw_cases", "offline_vaw_cases", "cyber_total_cases", "cyber_fraud",
        "female_pop_lakh", "population_lakh", "trai_subs_mn"]


def est(m, term):
    return {"rate_ratio": round(float(np.exp(m.coef()[term])), 3), "p": round(float(m.pvalue()[term]), 4),
            "states": int(m._data.state.nunique()), "n": int(m._N)}


def national(p):
    wb = pd.read_excel(ACCESS, "WorldBank_National", header=3)
    wb = wb.rename(columns={wb.columns[0]: "year"})[["year", "internet_users_mn"]]
    nat = p.groupby("year")[["cyber_vaw_cases", "offline_vaw_cases"]].sum(min_count=1).reset_index()
    nat = nat.merge(wb, on="year").dropna()
    out = {"years": [int(nat.year.min()), int(nat.year.max())]}
    for y in ["cyber_vaw_cases", "offline_vaw_cases"]:
        lx, ly = np.log(nat.internet_users_mn), np.log(nat[y])
        out[y] = {"elasticity": round(float(np.polyfit(lx, ly, 1)[0]), 2),
                  "corr_levels": round(float(pearsonr(lx, ly)[0]), 2),
                  "corr_growth": round(float(pearsonr(np.diff(lx), np.diff(ly))[0]), 2)}
    out["series"] = nat.round(2).to_dict("records")
    return out


def cross_state(p):
    out = {}
    q = p[p.year >= 2017]
    for acc in ["access_cams2023_15plus", "access_nss2017_5plus", "access_nfhs5_15to49_avg"]:
        out[acc] = {}
        for y, off in [("cyber_vaw_cases", "female_pop_lakh"), ("offline_vaw_cases", "female_pop_lakh"),
                       ("cyber_total_cases", "population_lakh"), ("cyber_fraud", "population_lakh")]:
            d = q.dropna(subset=[acc, y, off]).copy()
            s = d.groupby("state")[acc].first()
            d["z"] = d.state.map((s - s.mean()) / s.std())
            d["lo"] = np.log(d[off])
            m = pf.fepois(f"{y} ~ z | year", data=d, offset="lo", vcov={"CRV1": "state"})
            out[acc][y] = est(m, "z")
    return out


def merge_units(d, states, name):
    g = d[d.state.isin(states)].groupby("year")[SUMS].sum().reset_index()
    g["state"] = name
    return pd.concat([d[~d.state.isin(states)], g], ignore_index=True)


def within_state(p):
    d = p[p.year.between(2022, 2024)].dropna(subset=["trai_subs_per100", "cyber_vaw_cases"]).copy()
    d["trai_subs_mn"] = d.trai_subs_per100 * d.population_lakh / 1000  # connections, million

    def run(data, y="cyber_vaw_cases", extra=""):
        data = data.copy()
        data["trai_10"] = data.trai_subs_mn * 1000 / data.population_lakh / 10
        data["lo"] = np.log(data.female_pop_lakh)
        data["other_cyber"] = np.log(data.cyber_total_cases - data.cyber_vaw_cases + 1)
        m = pf.fepois(f"{y} ~ trai_10{extra} | state + year", data=data, offset="lo", vcov={"CRV1": "state"})
        return est(m, "trai_10")

    ncr = merge_units(d, ["Delhi", "Haryana"], "Delhi+Haryana")
    out = {
        "main_delhi_haryana_merged": run(ncr),
        "as_reported_unmerged": run(d),
        "drop_delhi": run(d[d.state != "Delhi"]),
        "merge_delhi_haryana_up": run(merge_units(d, ["Delhi", "Haryana", "Uttar Pradesh"], "NCR+UP")),
        "placebo_offline_vaw": run(ncr, "offline_vaw_cases"),
        "control_other_cyber_growth": run(ncr, extra=" + other_cyber"),
    }
    L = pd.concat([ncr.assign(cases=ncr.cyber_vaw_cases, cyber=1), ncr.assign(cases=ncr.offline_vaw_cases, cyber=0)])
    L["trai_10"] = L.trai_subs_mn * 1000 / L.population_lakh / 10
    L["tc"] = L.trai_10 * L.cyber
    m = pf.fepois("cases ~ tc | state^cyber + state^year + cyber^year", data=L, vcov={"CRV1": "state"})
    out["cyber_vs_offline"] = est(m, "tc")
    return out


def main():
    p = pd.read_csv(PANEL)
    res = {"A_national_trend": national(p), "B_cross_state_levels": cross_state(p),
           "C_within_state_trai": within_state(p)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps({k: v for k, v in res.items()}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
