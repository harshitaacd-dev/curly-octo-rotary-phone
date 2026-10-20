"""Part 1 over a longer period: sexual-content cyber crime by State, 2013-2024.

Usage:
    python scripts/part1_long.py        # writes data/analysis/state_category_year_long.csv
                                        #        analysis/models/part1_long_results.json

Why: cyber crimes against women (NCRB Table 9A.10) start in 2017. The closest series NCRB published
by State before that is sexual-content cyber crime (IT Act Sec 67 + 67A + 66E, child abuse material
excluded), 2013-2024. It counts offences, not female victims, and 2013-2015 is Sec 67 only.
National changes in definitions (2016 split of 67A/66E), law (2013 amendment) and prices (Jio, 2016)
hit every State at once and are absorbed by the category x year fixed effects.

Units: as in scripts/build_analysis_panels.py, plus Andhra Pradesh + Telangana merged for every year
(NCRB reports them as one unit in 2013): 34 units.

Models (Poisson PPML, SE clustered by State; rate ratio = exp(coef)):
  Step 2 long  cases ~ Cyber x Access x (year - 2013) | State x category + State x year + category x year
               Cyber = sexual-content cyber crime; comparison = five offline crimes against women.
               Also 2017-2024 only, 2013-2016 only, and a placebo with all other cyber crime.
  Step 1 pre   2013-2016, cases ~ z_access [+ z_income] | year, exposure = 2017 female population.
  National     log sexual-content cases on log internet users (World Bank), 2013-2024.
"""
import json, os, sys, warnings

import numpy as np
import pandas as pd
import pyfixest as pf

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
from build_analysis_panels import OFFLINE_WOMEN, access_measures, norm_state, merge_units, ACCESS_XLSX  # noqa: E402

CLEAN = "data/clean"
OUT_PANEL = "data/analysis/state_category_year_long.csv"
OUT_JSON = "analysis/models/part1_long_results.json"
YEARS = (2013, 2024)
ACCESS = ["access_nss2017_5plus", "access_cams2023_15plus", "access_nfhs5_15to49_avg"]
APTG = "Andhra Pradesh + Telangana"


def unit(s):
    s = norm_state(s)
    return APTG if s in ("Andhra Pradesh", "Telangana") else s


def build_panel():
    w = pd.read_csv(os.path.join(CLEAN, "state_women_cyber_panel.csv"))
    c = pd.read_csv(os.path.join(CLEAN, "state_cyber_sexual_abusive.csv"))
    w, c = w[w.row_type == "state_ut"].copy(), c[c.row_type == "state_ut"].copy()
    w["state"], c["state"] = w.state.map(unit), c.state.map(unit)
    w = w.groupby(["state", "year"], as_index=False)[["cyber_total_cases", "female_population_lakh"] + list(OFFLINE_WOMEN)].sum(min_count=1)
    c = c.groupby(["state", "year"], as_index=False)[["sexual_content_total"]].sum(min_count=1)
    sy = w.merge(c, on=["state", "year"], how="left")
    sy = sy[sy.year.between(*YEARS)]
    sy["other_cyber"] = sy.cyber_total_cases - sy.sexual_content_total

    rows = []
    for col, label, group in ([("sexual_content_total", "sexual-content cyber crime", "cyber"),
                               ("other_cyber", "all other cyber crime", "placebo")]
                              + [(k, v, "offline") for k, v in OFFLINE_WOMEN.items()]):
        d = sy[["state", "year", col]].rename(columns={col: "cases"})
        d["category"], d["group"] = label, group
        rows.append(d)
    p = pd.concat(rows).dropna(subset=["cases"])

    # Female population: NCRB from 2017; earlier years use each unit's 2017 figure (a fixed exposure).
    fp = sy[["state", "year", "female_population_lakh"]].copy()
    fp17 = fp[fp.year == 2017].set_index("state").female_population_lakh
    fp["female_pop_lakh"] = fp.female_population_lakh.fillna(fp.state.map(fp17))
    p = p.merge(fp[["state", "year", "female_pop_lakh"]], on=["state", "year"], how="left")

    # Access: survey shares for the merged AP + Telangana unit are weighted by 2017 female population.
    acc = pd.read_csv("data/analysis/state_access.csv").set_index("state")[ACCESS]
    raw = access_measures(ACCESS_XLSX)
    pop = pd.read_csv(os.path.join(CLEAN, "state_women_cyber_panel.csv"))
    pop = pop[(pop.year == 2017) & pop.state.isin(["Andhra Pradesh", "Telangana"])].set_index("state").female_population_lakh
    ap = {}
    for x in ACCESS:
        v = raw[x].reindex(["Andhra Pradesh", "Telangana"]) if x in raw else acc[x].reindex(["Andhra Pradesh", "Telangana"])
        ap[x] = float((v * pop).sum() / pop.sum()) if v.notna().all() else np.nan
    acc = acc.drop(index=["Andhra Pradesh", "Telangana"], errors="ignore")
    acc.loc[APTG] = pd.Series(ap)

    ctl = pd.read_csv("data/analysis/state_controls.csv").set_index("state")
    w17 = pd.read_csv(os.path.join(CLEAN, "state_women_cyber_panel.csv"))
    w17 = w17[(w17.year == 2017) & w17.state.isin(["Andhra Pradesh", "Telangana"])].set_index("state")
    inc = ctl.nsdp_pc_avg.reindex(["Andhra Pradesh", "Telangana"])
    ctl = ctl.drop(index=["Andhra Pradesh", "Telangana"], errors="ignore")
    ctl.loc[APTG, "nsdp_pc_avg"] = float((inc * w17.population_lakh).sum() / w17.population_lakh.sum())

    p = p.merge(acc, left_on="state", right_index=True, how="left")
    p = p.merge(ctl[["nsdp_pc_avg"]], left_on="state", right_index=True, how="left")
    p["sc"] = p.state + "|" + p.category
    p["st"] = p.state + "|" + p.year.astype(str)
    p["ct"] = p.category + "|" + p.year.astype(str)
    return p.sort_values(["state", "category", "year"]).reset_index(drop=True), sy


def zs(d, col):
    s = d.groupby("state")[col].first()
    return d.state.map((s - s.mean()) / s.std())


def res(m, term):
    t = m.tidy().loc[term]
    return {"rate_ratio": round(float(np.exp(t["Estimate"])), 3), "coef": round(float(t["Estimate"]), 4),
            "se": round(float(t["Std. Error"]), 4), "p": round(float(t["Pr(>|t|)"]), 4), "n": int(m._N)}


def model1(p, x, years=YEARS, treated="cyber", base=2013):
    d = p[p.group.isin([treated, "offline"]) & p.year.between(*years) & p[x].notna()].copy()
    d["z"] = zs(d, x)
    d["treat"] = (d.group == treated) * d.z * (d.year - base)
    m = pf.fepois("cases ~ treat | sc + st + ct", data=d, vcov={"CRV1": "state"})
    r = res(m, "treat"); r["states"] = int(d.state.nunique())
    return r


def step1_pre(p):
    d = p[(p.group == "cyber") & p.year.between(2013, 2016)].copy()
    d = d[d.access_nss2017_5plus.notna() & d.nsdp_pc_avg.notna()]
    d["ln_income"] = np.log(d.nsdp_pc_avg)
    d["z_access"], d["z_income"] = zs(d, "access_nss2017_5plus"), zs(d, "ln_income")
    d["lexp"] = np.log(d.female_pop_lakh)
    out = {}
    for name, rhs in {"no_controls": "z_access", "income": "z_access + z_income"}.items():
        m = pf.fepois(f"cases ~ {rhs} | year", data=d, vcov={"CRV1": "state"}, offset="lexp")
        out[name] = {t: res(m, t) for t in rhs.split(" + ")}
        out[name]["states"] = int(d.state.nunique())
    # Same models 2017-2024 on the same outcome and States, for comparison.
    d2 = p[(p.group == "cyber") & p.year.between(2017, 2024) & p.state.isin(d.state.unique())].copy()
    d2["ln_income"] = np.log(d2.nsdp_pc_avg)
    d2["z_access"], d2["z_income"] = zs(d2, "access_nss2017_5plus"), zs(d2, "ln_income")
    d2["lexp"] = np.log(d2.female_pop_lakh)
    for name, rhs in {"no_controls_2017_2024": "z_access", "income_2017_2024": "z_access + z_income"}.items():
        m = pf.fepois(f"cases ~ {rhs} | year", data=d2, vcov={"CRV1": "state"}, offset="lexp")
        out[name] = {t: res(m, t) for t in rhs.split(" + ")}
    return out


def national(sy):
    wb = pd.read_excel(ACCESS_XLSX, "WorldBank_National", header=3)[["year", "internet_users_mn"]]
    n = sy.groupby("year", as_index=False).sexual_content_total.sum().merge(wb, on="year")
    n = n[n.year.between(*YEARS)].dropna()
    lx, ly = np.log(n.internet_users_mn), np.log(n.sexual_content_total)
    b, a = np.polyfit(lx, ly, 1)
    r2 = float(np.corrcoef(lx, ly)[0, 1] ** 2)
    g = pd.DataFrame({"gx": lx.diff(), "gy": ly.diff()}).dropna()
    def corr_window(a0):
        gg = g[n.year.iloc[1:].values >= a0 + 1]
        return round(float(gg.gx.corr(gg.gy)), 3), len(gg)
    return {"years": n.year.tolist(), "internet_users_mn": n.internet_users_mn.round(0).tolist(),
            "sexual_content_cases": n.sexual_content_total.astype(int).tolist(),
            "elasticity": round(float(b), 3), "r2": round(r2, 3), "corr_levels_log": round(float(np.corrcoef(lx, ly)[0, 1]), 3),
            "corr_growth_2013_2024": corr_window(2013), "corr_growth_2017_2024": corr_window(2017)}


def main():
    p, sy = build_panel()
    os.makedirs(os.path.dirname(OUT_PANEL), exist_ok=True)
    p.to_csv(OUT_PANEL, index=False)
    out = {"units": int(p.state.nunique()), "model1_long": {}, "model1_checks": {}}
    for x in ACCESS:
        out["model1_long"][x] = model1(p, x)
    x = "access_nss2017_5plus"
    out["model1_checks"] = {
        "2017_2024_same_outcome": model1(p, x, years=(2017, 2024), base=2017),
        "2013_2016_only": model1(p, x, years=(2013, 2016)),
        "2014_2016_only": model1(p, x, years=(2014, 2016), base=2014),
        "2014_2024_drop_2013": model1(p, x, years=(2014, 2024), base=2014),
        "cams_2013_2016_only": model1(p, "access_cams2023_15plus", years=(2013, 2016)),
        "cams_2014_2016_only": model1(p, "access_cams2023_15plus", years=(2014, 2016), base=2014),
        "placebo_other_cyber": model1(p, x, treated="placebo"),
    }
    out["step1_pre"] = step1_pre(p)
    out["national"] = national(sy)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(out, open(OUT_JSON, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
