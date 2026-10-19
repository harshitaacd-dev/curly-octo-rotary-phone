"""Part 3: growth of police-recorded cyber crime against women versus growth of complaints to platforms.

Usage: python scripts/part3_models.py   (writes analysis/models/part3_results.json)

MAIN (share-adjusted): each side is measured against its own comparison group, so growth of the reporting
route itself is removed (complaints to Meta for every reason rose about 7x in 2023 with the amended IT Rules
and the Grievance Appellate Committee).
    NCRB: cases ~ Cyber x (year - 2022) | State x crime + State x year, 2022-2024, cyber crimes against women
          against the five offline crimes against women; SE clustered by State.
    Platform: count ~ Sexual x t | type + month, Jan 2022 - Dec 2024, sexual-content complaints against the
          platform's other complaints; robust SE.
    z-test of each platform's relative growth against NCRB's relative growth.
SECONDARY (raw growth, below): growth of the counts themselves, without comparison groups.

NCRB side (State x year, 2022-2024): cases ~ (year - 2022) | State, Poisson, SE clustered by State.
    exp(b) = yearly growth of recorded cyber crime against women.
Platform side (monthly, Jan 2022 - Dec 2024): for each platform, its sexual-content complaints
    (X: sexual + synthetic media) ~ years since Jan 2022 + month-of-year, Poisson, HAC SE (6 lags).
    exp(t) = yearly growth of that platform's complaints.
Comparison: z = (t - b) / sqrt(se_t^2 + se_b^2), the two sources being independent.
Pooled: OLS of log monthly complaints on time, platform and month-of-year effects, SE clustered by
    platform (only five clusters: a summary, not the main test).
Check: the same growth for each platform relative to its other complaints (complaint-route growth).
X stops at February 2025 (format change), so the 2022-2024 window is complete for every platform.
"""
import json, os, warnings

import numpy as np
import pandas as pd
import pyfixest as pf
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import norm

warnings.filterwarnings("ignore")
OUT = "analysis/models/part3_results.json"
PLATFORMS = ["Facebook", "Instagram", "X", "Snapchat", "Google"]


def ncrb():
    d = pd.read_csv("data/analysis/state_year_panel.csv")
    d = d[d.year.between(2022, 2024)].dropna(subset=["cyber_vaw_cases"]).copy()
    d["t"] = d.year - 2022
    m = pf.fepois("cyber_vaw_cases ~ t | state", data=d, vcov={"CRV1": "state"})
    return float(m.coef()["t"]), float(m.se()["t"])


def ncrb_relative():
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from estimate_models import model1_sample
    d = model1_sample(pd.read_csv("data/analysis/state_category_year_panel.csv"), "total")
    d = d[d.year.between(2022, 2024)].copy()
    d["x"] = d.cyber * (d.year - 2022)
    m = pf.fepois("cases ~ x | sc + st", data=d, vcov={"CRV1": "state"})
    return float(m.coef()["x"]), float(m.se()["x"])


def monthly():
    pm = pd.read_csv("data/analysis/platform_month_panel.csv")
    pm = pm[(pm.suspect_duplicate == 0) & pm.platform.isin(PLATFORMS) & pm.month.between("2022-01", "2024-12")].copy()
    pm["target"] = pm.category_group.isin(["sexual", "synthetic"]).astype(int)
    a = pm.groupby(["platform", "month", "target"])["count"].sum().reset_index()
    ym = pd.PeriodIndex(a.month, freq="M")
    a["t"] = (ym.year - 2022) + (ym.month - 1) / 12
    a["moy"] = ym.month
    return a


def main():
    b, sb = ncrb()
    rb, rsb = ncrb_relative()
    a = monthly()
    res = {"main_share_adjusted": {"ncrb_relative": {"growth_per_year": round(np.exp(rb), 3),
                                                     "ci95": [round(np.exp(rb - 1.96 * rsb), 3), round(np.exp(rb + 1.96 * rsb), 3)]},
                                   "platforms": {}},
           "ncrb": {"growth_per_year": round(np.exp(b), 3), "se": round(sb, 4),
                    "ci95": [round(np.exp(b - 1.96 * sb), 3), round(np.exp(b + 1.96 * sb), 3)]}, "platforms": {}}
    for p in PLATFORMS:
        s = a[(a.platform == p) & (a.target == 1)]
        m = smf.glm("count ~ t + C(moy)", s, family=sm.families.Poisson()).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
        t, st = m.params["t"], m.bse["t"]
        z = (t - b) / np.hypot(st, sb)
        # relative to the platform's other complaints (route growth removed)
        r = a[a.platform == p].copy()
        r["x"] = r.target * r.t
        mr = pf.fepois("count ~ x | target + month", data=r, vcov="hetero")
        rt, rst = float(mr.coef()["x"]), float(mr.se()["x"])
        res["main_share_adjusted"]["platforms"][p] = {
            "relative_growth_per_year": round(np.exp(rt), 3),
            "ci95": [round(np.exp(rt - 1.96 * rst), 3), round(np.exp(rt + 1.96 * rst), 3)],
            "p_diff_vs_ncrb_relative": round(2 * norm.sf(abs((rt - rb) / np.hypot(rst, rsb))), 4)}
        res["platforms"][p] = {
            "growth_per_year": round(np.exp(t), 3), "ci95": [round(np.exp(t - 1.96 * st), 3), round(np.exp(t + 1.96 * st), 3)],
            "p_diff_vs_ncrb": round(2 * norm.sf(abs(z)), 4), "months": int(len(s)),
            "relative_to_other_complaints": round(float(np.exp(mr.coef()["x"])), 3),
            "relative_p": round(float(mr.pvalue()["x"]), 4)}
    s = a[a.target == 1].copy()
    s["lc"] = np.log(s["count"] + 1)
    m = smf.ols("lc ~ t + C(platform) + C(moy)", s).fit(cov_type="cluster", cov_kwds={"groups": s.platform})
    z = (m.params["t"] - b) / np.hypot(m.bse["t"], sb)
    res["pooled"] = {"growth_per_year": round(float(np.exp(m.params["t"])), 3), "p_diff_vs_ncrb": round(2 * norm.sf(abs(z)), 4)}
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
