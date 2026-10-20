"""The Jio shock and recorded sexual-content cyber crime, by State, 2013-2024.

Usage:
    python scripts/jio_models.py [--perms 500]
    Inputs: data/analysis/state_category_year_long.csv (scripts/part1_long.py),
            data/analysis/state_jio.csv (scripts/jio_coverage.py), data/analysis/state_controls.csv
    Writes analysis/models/jio_results.json and data/analysis/state_category_year_long_jio.csv

Design, following "Mobile Internet and Collective Action: Evidence from India's Jio Shock"
(SSRN 6959526): Jio launched on 5 September 2016 and cut data prices by over 90 percent everywhere at
once; States differed in how much of their population Jio's network reached at launch. Continuous-
treatment difference-in-differences, Poisson PPML, SE clustered by State. Coverage enters per 10
percentage points, so rate ratio = exp(b) is the change for a State with 10 pp more coverage.

  Main (triple difference, as in Models 1-2):
      cases ~ Cyber x Post x Jio | State x crime + State x year + crime x year
      Cyber = sexual-content cyber crime; comparison = five offline crimes against women.
  Paper's version (double difference, one outcome at a time):
      cases ~ Post x Jio | State + year, exposure = female population
      Outcomes: sexual-content cyber crime; all other cyber crime; offline crimes against women (placebo).
  Post = 2017 onwards (first full year; free service until March 2017). Window 2013-2022, before the AI
  period; 2013-2024 as a check. Coverage = share of 2016 population within 5 km of a Jio cell first
  seen by 31 December 2016 (OpenCellID). Checks: Post from 2016; cells seen by September 2016 or March
  2017; 7 km radius; year x urban share and year x income; event study (base 2016) with a joint
  pre-trend test; placebo date 2015 on 2013-2016 only; randomisation inference.
"""
import argparse, json

import numpy as np
import pandas as pd
import pyfixest as pf

PANEL = "data/analysis/state_category_year_long.csv"
JIO = "data/analysis/state_jio.csv"
CTL = "data/analysis/state_controls.csv"
OUT = "analysis/models/jio_results.json"
MAIN = "jio_cov5km_dec2016"
APTG = "Andhra Pradesh + Telangana"


def jio_units():
    j = pd.read_csv(JIO).set_index("state")
    cov = [c for c in j.columns if c.startswith("jio_cov")]
    ap = j.loc[["Andhra Pradesh", "Telangana"]]
    merged = (ap[cov].mul(ap.pop2016_mn, axis=0).sum() / ap.pop2016_mn.sum())
    j = j.drop(index=["Andhra Pradesh", "Telangana"])
    j.loc[APTG, cov] = merged
    j.loc[APTG, "pop2016_mn"] = ap.pop2016_mn.sum()
    return j[cov + ["pop2016_mn"]]


def controls():
    c = pd.read_csv(CTL).set_index("state")
    ap = c.loc[["Andhra Pradesh", "Telangana"]].mean()
    c = c.drop(index=["Andhra Pradesh", "Telangana"])
    c.loc[APTG] = ap
    c["ln_income"] = np.log(c.nsdp_pc_avg)
    return c[["ln_income", "urban_share_cams"]]


def load():
    p = pd.read_csv(PANEL)
    p = p.merge(jio_units(), left_on="state", right_index=True, how="left")
    p = p.merge(controls(), left_on="state", right_index=True, how="left")
    return p


def res(m, term):
    t = m.tidy().loc[term]
    return {"rate_ratio": round(float(np.exp(t["Estimate"])), 3), "coef": round(float(t["Estimate"]), 4),
            "se": round(float(t["Std. Error"]), 4), "p": round(float(t["Pr(>|t|)"]), 4), "n": int(m._N)}


def triple(p, cov=MAIN, years=(2013, 2022), post=2017, treated="cyber", extra="", perms=0):
    d = p[p.group.isin([treated, "offline"]) & p.year.between(*years) & p[cov].notna()].copy()
    d["j"] = d[cov] * 10
    d["cyb"] = (d.group == treated).astype(int)
    d["treat"] = d.cyb * (d.year >= post) * d.j
    rhs = "treat"
    if extra:
        for v in extra.split("+"):
            v = v.strip()
            d = d[d[v].notna()]
            d[f"cy_{v}"] = d.cyb * (d.year - years[0]) * (d[v] - d.groupby("state")[v].first().mean())
            rhs += f" + cy_{v}"
    m = pf.fepois(f"cases ~ {rhs} | sc + st + ct", data=d, vcov={"CRV1": "state"})
    r = res(m, "treat"); r["states"] = int(d.state.nunique())
    if perms:
        r["ri_p"] = ri(d, rhs, float(m.coef()["treat"]), perms, post)
    return r


def ri(d, rhs, actual, perms, post, seed=1):
    rng = np.random.default_rng(seed)
    js = d.groupby("state").j.first()
    hits = done = 0
    for _ in range(perms):
        perm = pd.Series(rng.permutation(js.values), index=js.index)
        dd = d.copy()
        dd["treat"] = dd.cyb * (dd.year >= post) * dd.state.map(perm)
        try:
            b = float(pf.fepois(f"cases ~ {rhs} | sc + st + ct", data=dd, vcov="iid").coef()["treat"])
        except Exception:
            continue
        done += 1
        hits += abs(b) >= abs(actual)
    return round(hits / done, 4) if done else None


def double(p, group, cov=MAIN, years=(2013, 2022), post=2017):
    """The paper's own design: one outcome, State and year fixed effects, female population exposure."""
    d = p[p.year.between(*years) & p[cov].notna()]
    d = d[d.group == group] if group != "offline" else d[d.group == "offline"]
    d = d.groupby(["state", "year"], as_index=False).agg(cases=("cases", "sum"), fp=("female_pop_lakh", "first"), cov=(cov, "first"))
    d["treat"] = (d.year >= post) * d["cov"] * 10
    d["lexp"] = np.log(d.fp)
    m = pf.fepois("cases ~ treat | state + year", data=d, vcov={"CRV1": "state"}, offset="lexp")
    r = res(m, "treat"); r["states"] = int(d.state.nunique())
    return r


def event(p, cov=MAIN, years=(2013, 2022), base=2016):
    d = p[p.group.isin(["cyber", "offline"]) & p.year.between(*years) & p[cov].notna()].copy()
    d["j"] = d[cov] * 10
    d["cyb"] = (d.group == "cyber").astype(int)
    terms = []
    for y in range(years[0], years[1] + 1):
        if y == base:
            continue
        d[f"e{y}"] = d.cyb * (d.year == y) * d.j
        terms.append(f"e{y}")
    m = pf.fepois("cases ~ " + " + ".join(terms) + " | sc + st + ct", data=d, vcov={"CRV1": "state"})
    t = m.tidy()
    out = {y: {"coef": round(float(t.loc[f"e{y}", "Estimate"]), 4), "p": round(float(t.loc[f"e{y}", "Pr(>|t|)"]), 4)}
           for y in range(years[0], years[1] + 1) if y != base}
    pre = [f"e{y}" for y in range(years[0], base)]
    b = m.coef()[pre].values
    V = m._vcov[np.ix_([terms.index(x) for x in pre], [terms.index(x) for x in pre])]
    w = float(b @ np.linalg.solve(V, b))
    from scipy.stats import chi2
    out["pretrend_chi2"] = round(w, 2)
    out["pretrend_df"] = len(pre)
    out["pretrend_p"] = round(float(chi2.sf(w, len(pre))), 4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=500)
    a = ap.parse_args()
    p = load()
    p.to_csv("data/analysis/state_category_year_long_jio.csv", index=False)
    out = {
        "coverage_summary": p.groupby("state")[MAIN].first().describe().round(3).to_dict(),
        "main_2013_2022": triple(p, perms=a.perms),
        "checks": {
            "window_2013_2024": triple(p, years=(2013, 2024)),
            "post_from_2016": triple(p, post=2016),
            "cells_seen_sep2016": triple(p, cov="jio_cov5km_sep2016"),
            "cells_seen_mar2017": triple(p, cov="jio_cov5km_mar2017"),
            "radius_7km": triple(p, cov="jio_cov7km_dec2016"),
            "drop_2013": triple(p, years=(2014, 2022)),
            "year_x_urban_income": triple(p, extra="urban_share_cams + ln_income"),
            "placebo_date_2015_pre_only": triple(p, years=(2013, 2016), post=2015),
            "other_cyber_as_treated": triple(p, treated="placebo"),
        },
        "paper_design_double_difference": {
            "sexual_content": double(p, "cyber"),
            "other_cyber": double(p, "placebo"),
            "offline_women_placebo": double(p, "offline"),
        },
        "event_study": event(p),
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
