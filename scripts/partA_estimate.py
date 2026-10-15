"""Part A: did Grok's image-generation releases raise synthetic-media grievances on X in India?

Usage: python scripts/partA_estimate.py data/clean/platform_grievances_monthly.csv analysis/partA

Poisson regressions with fixed effects (pyfixest.fepois) on monthly grievance counts.

Events (X's reporting month runs from the 26th to the 25th, labelled by the month it ends in):
  E1  Grok-2 with image generation, 13 Aug 2024    -> first treated month 2024-08
  E2  Grok + Aurora image generator for all users, ~8-12 Dec 2024 -> first treated month 2024-12
  Placebo: Grok-1 (text only, paid users), Nov 2023 -> 2023-11
Main sample ends 2025-02: from 2025-03 X's synthetic-media counts drop to ~0 together with a
collapse in total grievances (a reporting change), and from 2025-09 X switched to shares.

Models
  M1  within X: synthetic vs X's other categories, category FE + month FE
  M2  M1 + synthetic x election-month control (elections coded from approximate polling /
      counting months, see ELECTIONS)
  M3  event study: synthetic x month dummies from 2023-08, reference = months before 2023-08
  M4  placebo event: Grok-1 (Nov 2023), sample to 2024-07
  M5  randomisation inference across categories: each X category in turn treated as if it
      were synthetic media
  M6  randomisation inference across dates: fake event dates in 2022-01..2023-12
  M7  cross-platform triple difference for groups that exist on every platform (sexual
      content, impersonation, harassment): X x group x post vs Facebook / Instagram / Google,
      FE platform x category, platform x month, group x month
  R1  robustness: sample through 2025-08 with a dummy for X's post-Mar 2025 reporting regime
  R2  robustness: log(1+count) OLS version of M2
"""
import json, os, sys
import numpy as np
import pandas as pd
import pyfixest as pf

ELECTIONS = {  # X reporting months covering campaign end / polling / counting of major elections
    "2022-02": "UP, Punjab, Uttarakhand, Goa, Manipur", "2022-03": "UP, Punjab, Uttarakhand, Goa, Manipur",
    "2022-11": "Himachal Pradesh, Gujarat", "2022-12": "Gujarat",
    "2023-05": "Karnataka",
    "2023-11": "MP, Rajasthan, Chhattisgarh, Telangana, Mizoram", "2023-12": "MP, Rajasthan, Chhattisgarh, Telangana",
    "2024-04": "Lok Sabha", "2024-05": "Lok Sabha", "2024-06": "Lok Sabha",
    "2024-09": "Haryana, J&K", "2024-10": "Haryana, J&K",
    "2024-11": "Maharashtra, Jharkhand",
    "2025-01": "Delhi", "2025-02": "Delhi",
}
E1, E2, G1 = "2024-08", "2024-12", "2023-11"
SYN = "Misinformation / Synthetic and Manipulated Media"


def x_panel(p, end="2025-02"):
    x = p[(p.platform == "X") & (p.month <= end)].copy()
    # balanced on categories present throughout; Ban Evasion (2024+) kept, FE handle entry
    x["syn"] = (x.category == SYN).astype(int)
    x["elec"] = x.month.isin(ELECTIONS).astype(int)
    x["post1"] = ((x.month >= E1) & (x.month < E2)).astype(int)
    x["post2"] = (x.month >= E2).astype(int)
    x["syn_p1"], x["syn_p2"], x["syn_elec"] = x.syn * x.post1, x.syn * x.post2, x.syn * x.elec
    return x


def fit(fml, data, vcov="hetero"):
    return pf.fepois(fml, data=data, vcov=vcov)


def row(model, name, terms):
    t = model.tidy()
    out = {"model": name, "n": int(model._N)}
    for term in terms:
        if term in t.index:
            b, se, p = t.loc[term, "Estimate"], t.loc[term, "Std. Error"], t.loc[term, "Pr(>|t|)"]
            out[term] = {"coef": round(float(b), 3), "se": round(float(se), 3), "p": round(float(p), 4),
                         "irr": round(float(np.exp(b)), 2)}
    return out


def main(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    p = pd.read_csv(src)
    p["count"] = p["count"].clip(lower=0)
    res = []

    x = x_panel(p)
    m1 = fit("count ~ syn_p1 + syn_p2 | category + month", x)
    res.append(row(m1, "M1 within-X DiD", ["syn_p1", "syn_p2"]))
    m1c = fit("count ~ syn_p1 + syn_p2 | category + month", x, vcov={"CRV1": "category"})
    res.append(row(m1c, "M1 clustered by category", ["syn_p1", "syn_p2"]))
    m2 = fit("count ~ syn_p1 + syn_p2 + syn_elec | category + month", x)
    res.append(row(m2, "M2 + synthetic x election", ["syn_p1", "syn_p2", "syn_elec"]))

    # M3 event study
    months = sorted(x.month.unique())
    es_months = [m for m in months if m >= "2023-08"]
    for m in es_months:
        x[f"es_{m}"] = ((x.month == m) & (x.syn == 1)).astype(int)
    es_terms = [f"es_{m}" for m in es_months]
    xr = x.rename(columns={t: t.replace("-", "_") for t in es_terms})
    es_terms_r = [t.replace("-", "_") for t in es_terms]
    m3 = fit("count ~ " + " + ".join(es_terms_r) + " | category + month", xr)
    es = m3.tidy().loc[es_terms_r, ["Estimate", "Std. Error"]].reset_index()
    es["month"] = es_months
    es["elec"] = es.month.isin(ELECTIONS)
    es.to_csv(os.path.join(outdir, "event_study.csv"), index=False)

    # M4 placebo: Grok-1
    xg = x_panel(p, end="2024-07")
    xg["syn_g1"] = xg.syn * (xg.month >= G1).astype(int)
    m4 = fit("count ~ syn_g1 + syn_elec | category + month", xg)
    res.append(row(m4, "M4 placebo Grok-1 (Nov 2023)", ["syn_g1", "syn_elec"]))

    # M5 randomisation inference across categories
    ri = []
    for c in sorted(x.category.unique()):
        d = x.copy()
        d["t"] = (d.category == c).astype(int)
        d["t_p1"], d["t_p2"], d["t_elec"] = d.t * d.post1, d.t * d.post2, d.t * d.elec
        try:
            m = fit("count ~ t_p1 + t_p2 + t_elec | category + month", d)
            b = m.coef()
            ri.append({"category": c, "b_p1": float(b["t_p1"]), "b_p2": float(b["t_p2"])})
        except Exception as e:  # categories absent before the event cannot be estimated
            ri.append({"category": c, "b_p1": np.nan, "b_p2": np.nan, "note": str(e)[:60]})
    ri = pd.DataFrame(ri)
    ri.to_csv(os.path.join(outdir, "ri_categories.csv"), index=False)
    valid = ri.dropna(subset=["b_p1", "b_p2"])
    syn = valid[valid.category == SYN].iloc[0]
    ri_p = {k: round(float((valid[k] >= syn[k]).mean()), 3) for k in ("b_p1", "b_p2")}
    res.append({"model": "M5 randomisation inference across categories", "n_categories": int(len(valid)),
                "rank_p_value": ri_p})

    # M6 randomisation inference across fake event dates (pre-period only)
    pre = x_panel(p, end="2024-03")
    fake = []
    for fm in [m for m in sorted(pre.month.unique()) if "2022-01" <= m <= "2023-12"]:
        d = pre.copy()
        d["t"] = d.syn * (d.month >= fm).astype(int)
        m = fit("count ~ t + syn_elec | category + month", d)
        fake.append({"fake_event": fm, "b": float(m.coef()["t"])})
    fake = pd.DataFrame(fake)
    fake.to_csv(os.path.join(outdir, "ri_dates.csv"), index=False)
    res.append({"model": "M6 placebo event dates 2022-01..2023-12 (pre-period)",
                "n_dates": int(len(fake)), "max_b": round(float(fake.b.max()), 3),
                "share_ge_M2_p1": round(float((fake.b >= m2.coef()["syn_p1"]).mean()), 3),
                "share_ge_M2_p2": round(float((fake.b >= m2.coef()["syn_p2"]).mean()), 3)})

    # M7 cross-platform triple difference
    c = p[(p.month <= "2025-02") & (p.month >= "2021-06") & p.group.isin(["sexual", "impersonation", "harassment", "placebo"])].copy()
    c["pc"] = c.platform + "|" + c.category
    c["pm"] = c.platform + "|" + c.month
    c["gm"] = c.group + "|" + c.month
    c["isx"] = (c.platform == "X").astype(int)
    c["p1"] = ((c.month >= E1) & (c.month < E2)).astype(int)
    c["p2"] = (c.month >= E2).astype(int)
    terms = []
    for g in ("sexual", "impersonation", "harassment"):
        for k in ("p1", "p2"):
            col = f"x_{g}_{k}"
            c[col] = c.isx * (c.group == g).astype(int) * c[k]
            terms.append(col)
    m7 = fit("count ~ " + " + ".join(terms) + " | pc + pm + gm", c, vcov={"CRV1": "pc"})
    res.append(row(m7, "M7 cross-platform triple difference (X vs Facebook/Instagram/Google)", terms))

    # R1 longer sample with regime dummy
    xl = x_panel(p, end="2025-08")
    xl["syn_regime"] = xl.syn * (xl.month >= "2025-03").astype(int)
    r1 = fit("count ~ syn_p1 + syn_p2 + syn_elec + syn_regime | category + month", xl)
    res.append(row(r1, "R1 sample to 2025-08 with post-Mar-2025 regime dummy", ["syn_p1", "syn_p2", "syn_elec", "syn_regime"]))

    # R2 log-OLS
    x["lc"] = np.log1p(x["count"])
    r2 = pf.feols("lc ~ syn_p1 + syn_p2 + syn_elec | category + month", data=x, vcov="hetero")
    t = r2.tidy()
    res.append({"model": "R2 log(1+count) OLS", "n": int(r2._N),
                **{k: {"coef": round(float(t.loc[k, "Estimate"]), 3), "se": round(float(t.loc[k, "Std. Error"]), 3),
                       "p": round(float(t.loc[k, "Pr(>|t|)"]), 4)} for k in ("syn_p1", "syn_p2", "syn_elec")}})

    with open(os.path.join(outdir, "results.json"), "w") as f:
        json.dump(res, f, indent=2)
    for r in res:
        print(json.dumps(r))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
