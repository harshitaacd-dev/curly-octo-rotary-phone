"""Estimate Models 1 and 2 of research/econometric-specification.md on the analysis panels.

Usage:
    python scripts/estimate_models.py                     # writes analysis/models/
    python scripts/estimate_models.py --perms 0           # skip randomisation inference (faster)

Panel: data/analysis/state_category_year_panel.csv (35 State/UT units x crime category x 2017-2024).
Exposure columns are fixed per State and come from data/analysis/state_access.csv (merged into the panel).

Estimator: Poisson PPML with fixed effects (pyfixest.fepois), standard errors clustered by State.
Fixed effects: State x category, State x year, category x year. Any offset that varies by State x year
(female population) is absorbed by the State x year effects, so none is included.
Exposure is standardised across the States in each estimation sample (mean 0, SD 1), so a coefficient
is the extra proportional change for a State one SD more exposed: rate ratio = exp(coef).

Model 1  internet access and the growth of cyber crime against women, 2017-2024
    cases ~ Cyber_c x Access_s x (year - 2017) | state x category + state x year + category x year
    Main outcome: all cyber crimes against women summed into one category (robust to how States
    split cases across heads). Comparison: five offline crimes against women.
Model 2  the generative-AI boom
    cases ~ Cyber_c x Post_t x Exposure_s | same fixed effects;  Post = 2023-2024
    Treated: all cyber crimes against women summed into one category (as in Model 1).
    Comparison: offline crimes against women. Each cyber head is also run separately.
Placebo: cyber fraud in place of the cyber-crime-against-women outcome.
Randomisation inference: exposure reassigned across States --perms times; p = share of permuted
|coef| >= actual |coef|.
"""
import argparse, json, os, warnings

import numpy as np
import pandas as pd
import pyfixest as pf

warnings.filterwarnings("ignore")

PANEL = "data/analysis/state_category_year_panel.csv"
ACCESS_M1 = ["access_cams2023_15plus", "access_nss2017_5plus", "access_nfhs5_15to49_avg", "access_cams2023_15to24"]
EXPOSURE_M2 = ["access_nfhs5_15to49_avg", "access_cams2023_15plus", "ads_nudify_to_genai_post",
               "ads_nudify_per_lakh_post", "trends_deepfake_awareness_pre", "trends_face_swap_pre"]
FE = "sc + st + ct"


def prep(d):
    d = d.copy()
    d["sc"] = d.state + "|" + d.category
    d["st"] = d.state + "|" + d.year.astype(str)
    d["ct"] = d.category + "|" + d.year.astype(str)
    return d


def standardise(d, col):
    s = d.groupby("state")[col].first()
    z = (s - s.mean()) / s.std()
    return d.state.map(z)


def fit(d, rhs, fe=FE):
    m = pf.fepois(f"cases ~ {rhs} | {fe}", data=d, vcov={"CRV1": "state"})
    return m


def coef(m, term):
    t = m.tidy().loc[term]
    return {"coef": round(float(t["Estimate"]), 4), "se": round(float(t["Std. Error"]), 4),
            "p": round(float(t["Pr(>|t|)"]), 4), "rate_ratio": round(float(np.exp(t["Estimate"])), 3),
            "n": int(m._N), "states": int(d_states(m))}


def d_states(m):
    try:
        return m._data.state.nunique()
    except Exception:
        return -1


def ri_pvalue(d, build_treat, actual, perms, seed=1):
    """Reassign the State exposure at random; refit; share of |coef| >= |actual|."""
    if perms <= 0:
        return None
    rng = np.random.default_rng(seed)
    states = d.state.unique()
    z = d.groupby("state")["z"].first()
    hits, done = 0, 0
    for _ in range(perms):
        perm = pd.Series(rng.permutation(z.values), index=z.index)
        dd = d.copy()
        dd["z"] = dd.state.map(perm)
        dd["treat"] = build_treat(dd)
        try:
            b = float(fit(dd, "treat").tidy().loc["treat", "Estimate"])
        except Exception:
            continue
        done += 1
        hits += abs(b) >= abs(actual)
    return round(hits / done, 4) if done else None


# ---------------------------------------------------------------- Model 1
def model1_sample(p, outcome="total"):
    """Cyber crimes against women (summed, or by head) + offline crimes against women."""
    off = p[p.category_group == "offline_women"]
    cyb = p[p.category_group == "cyber_women"]
    if outcome == "total":
        keep = [c for c in p.columns if c not in ("category", "cases", "is_ai_susceptible")]
        first = cyb.groupby(["state", "year"], as_index=False).first()[[c for c in keep if c not in ("category_group",)]]
        tot = cyb.groupby(["state", "year"], as_index=False)["cases"].sum().merge(first, on=["state", "year"])
        tot["category"], tot["category_group"], tot["is_ai_susceptible"] = "cyber crimes against women (all)", "cyber_women", 0
        cyb = tot
    elif outcome == "placebo":
        cyb = p[p.category_group == "cyber_placebo"].copy()
    d = pd.concat([cyb, off], ignore_index=True)
    d["cyber"] = (d.category_group != "offline_women").astype(int)
    return prep(d)


def run_model1(p, perms):
    out = {}
    for x in ACCESS_M1:
        d = model1_sample(p, "total")
        d = d[d[x].notna()].copy()
        d["z"] = standardise(d, x)
        d["treat"] = d.cyber * d.z * (d.year - 2017)
        m = fit(d, "treat")
        r = coef(m, "treat")
        r["states"] = int(d.state.nunique())
        if x == ACCESS_M1[0]:
            r["ri_p"] = ri_pvalue(d, lambda dd: dd.cyber * dd.z * (dd.year - 2017), r["coef"], perms)
        out[x] = r
    # By head (secondary): each cyber head against the offline crimes
    d = model1_sample(p, "heads")
    d = d[d[ACCESS_M1[0]].notna()].copy()
    d["z"] = standardise(d, ACCESS_M1[0])
    heads = {}
    for h in sorted(d[d.cyber == 1].category.unique()):
        dh = d[(d.cyber == 0) | (d.category == h)].copy()
        dh["treat"] = dh.cyber * dh.z * (dh.year - 2017)
        try:
            heads[h] = coef(fit(dh, "treat"), "treat")
        except Exception as e:
            heads[h] = f"failed ({type(e).__name__})"
    # Placebo: cyber fraud
    dp = model1_sample(p, "placebo")
    dp = dp[dp[ACCESS_M1[0]].notna()].copy()
    dp["z"] = standardise(dp, ACCESS_M1[0])
    dp["treat"] = dp.cyber * dp.z * (dp.year - 2017)
    placebo = coef(fit(dp, "treat"), "treat")
    # Event study (base 2017)
    d = model1_sample(p, "total")
    d = d[d[ACCESS_M1[0]].notna()].copy()
    d["z"] = standardise(d, ACCESS_M1[0])
    years = sorted(d.year.unique())
    for y in years:
        d[f"es{y}"] = d.cyber * d.z * (d.year == y)
    terms = [f"es{y}" for y in years if y != 2017]
    ev = fit(d, " + ".join(terms)).tidy().loc[terms, ["Estimate", "Std. Error", "Pr(>|t|)"]]
    ev.index = [int(i[2:]) for i in ev.index]
    ev.loc[2017] = [0.0, 0.0, np.nan]
    # Robustness on the main exposure
    rob = {}
    for name, cond in {"drop_2020": lambda x: x.year != 2020, "drop_2024": lambda x: x.year != 2024,
                       "drop_KA_TG": lambda x: ~x.state.isin(["Karnataka", "Telangana"])}.items():
        dd = model1_sample(p, "total")
        dd = dd[dd[ACCESS_M1[0]].notna() & cond(dd)].copy()
        dd["z"] = standardise(dd, ACCESS_M1[0])
        dd["treat"] = dd.cyber * dd.z * (dd.year - 2017)
        rob[name] = coef(fit(dd, "treat"), "treat")
    return {"by_exposure": out, "by_head": heads, "placebo_cyber_fraud": placebo, "robustness": rob}, ev.sort_index()


# ---------------------------------------------------------------- Model 2
def model2_sample(p, comparison="offline", treated="all"):
    """Treated: all cyber crimes against women summed into one category (or cyber fraud for the placebo).
    Comparison: offline crimes against women."""
    d = model1_sample(p, "placebo" if treated == "placebo" else "total")
    d["ai"] = d.cyber
    d["post"] = (d.year >= 2023).astype(int)
    return d


def run_model2(p, perms):
    out = {}
    for x in EXPOSURE_M2:
        d = model2_sample(p)
        d = d[d[x].notna()].copy()
        d["z"] = standardise(d, x)
        d["treat"] = d.ai * d.post * d.z
        r = coef(fit(d, "treat"), "treat")
        r["states"] = int(d.state.nunique())
        if x in (EXPOSURE_M2[0], "ads_nudify_to_genai_post"):
            r["ri_p"] = ri_pvalue(d, lambda dd: dd.ai * dd.post * dd.z, r["coef"], perms)
        out[x] = r
    main = EXPOSURE_M2[0]
    # Within-cyber comparison and placebo
    extra = {}
    for name, kw in {"placebo_cyber_fraud": dict(treated="placebo")}.items():
        d = model2_sample(p, **kw)
        d = d[d[main].notna()].copy()
        d["z"] = standardise(d, main)
        d["treat"] = d.ai * d.post * d.z
        extra[name] = coef(fit(d, "treat"), "treat")
    # Fake shock years (placebo timing), using 2017-2022 only
    fake = {}
    for fy in (2019, 2020, 2021):
        d = model2_sample(p)
        d = d[d[main].notna() & (d.year <= 2022)].copy()
        d["z"] = standardise(d, main)
        d["treat"] = d.ai * (d.year >= fy).astype(int) * d.z
        fake[str(fy)] = coef(fit(d, "treat"), "treat")
    # By head
    heads = {}
    d = model1_sample(p, "heads")
    d["ai"], d["post"] = d.cyber, (d.year >= 2023).astype(int)
    d = d[d[main].notna()].copy()
    d["z"] = standardise(d, main)
    for h in sorted(d[d.ai == 1].category.unique()):
        dh = d[(d.ai == 0) | (d.category == h)].copy()
        dh["treat"] = dh.ai * dh.post * dh.z
        heads[h] = coef(fit(dh, "treat"), "treat")
    # Event study (base 2022) with joint pre-trend test
    evs, pre_p = {}, {}
    for x in (main, "ads_nudify_to_genai_post"):
        d = model2_sample(p)
        d = d[d[x].notna()].copy()
        d["z"] = standardise(d, x)
        years = sorted(d.year.unique())
        for y in years:
            d[f"es{y}"] = d.ai * d.z * (d.year == y)
        terms = [f"es{y}" for y in years if y != 2022]
        m = fit(d, " + ".join(terms))
        ev = m.tidy().loc[terms, ["Estimate", "Std. Error", "Pr(>|t|)"]]
        ev.index = [int(i[2:]) for i in ev.index]
        ev.loc[2022] = [0.0, 0.0, np.nan]
        evs[x] = ev.sort_index()
        pre = [t for t in terms if int(t[2:]) < 2022]
        try:
            R = np.zeros((len(pre), len(terms)))
            for i, t in enumerate(pre):
                R[i, terms.index(t)] = 1
            w = m.wald_test(R=R)
            pre_p[x] = round(float(np.asarray(w.iloc[-1] if hasattr(w, "iloc") else w["pvalue"]).ravel()[-1]), 4)
        except Exception as e:
            pre_p[x] = f"not computed ({type(e).__name__})"
    # Robustness
    rob = {}
    for name, cond in {"drop_2020": lambda x: x.year != 2020, "drop_2024": lambda x: x.year != 2024,
                       "drop_KA_TG": lambda x: ~x.state.isin(["Karnataka", "Telangana"])}.items():
        dd = model2_sample(p)
        dd = dd[dd[main].notna() & cond(dd)].copy()
        dd["z"] = standardise(dd, main)
        dd["treat"] = dd.ai * dd.post * dd.z
        rob[name] = coef(fit(dd, "treat"), "treat")
    return {"by_exposure": out, "placebo_cyber_fraud": extra["placebo_cyber_fraud"],
            "fake_shock_years": fake, "by_head": heads, "pretrend_joint_p": pre_p, "robustness": rob}, evs


# ---------------------------------------------------------------- labelling controls
def labelling_breaks(threshold=0.30, min_cases=20):
    """State-years where NCRB recording practice jumps: |change| in the IT Act share of cyber cases or in the
    'other' share of cyber crimes against women above `threshold`, in years with >= min_cases cases.
    Returns State x year with it_share, other_share, brk (1 in a break year) and regime (breaks so far)."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from build_analysis_panels import norm_state
    w = pd.read_csv("data/clean/state_women_cyber_panel.csv")
    w = w[(w.row_type == "state_ut") & w.year.between(2017, 2024)].copy()
    w["state"] = w.state.map(norm_state)
    g = w.groupby(["state", "year"])[["cyber_it_act_total", "cyber_total_cases"]].sum(min_count=1).reset_index()
    sy = pd.read_csv("data/analysis/state_year_panel.csv")[["state", "year", "cyber_vaw_other", "cyber_vaw_cases"]]
    g = g.merge(sy, on=["state", "year"]).sort_values(["state", "year"])
    g["it_share"] = g.cyber_it_act_total / g.cyber_total_cases
    g["other_share"] = g.cyber_vaw_other / g.cyber_vaw_cases
    big = (g.cyber_total_cases >= min_cases) & (g.cyber_vaw_cases >= min_cases)
    jump = (g.groupby("state").it_share.diff().abs() > threshold) | (g.groupby("state").other_share.diff().abs() > threshold)
    g["brk"] = (big & jump).astype(int)
    g["regime"] = g.groupby("state").brk.cumsum()
    return g[["state", "year", "it_share", "other_share", "brk", "regime"]]


def run_labelling(p, model):
    """Main specification of Model 1 or 2 under three labelling controls."""
    br = labelling_breaks()
    break_states = set(br[br.brk == 1].state)
    x = ACCESS_M1[0] if model == 1 else EXPOSURE_M2[0]

    def sample():
        d = model1_sample(p, "total")
        d = d.merge(br, on=["state", "year"], how="left")
        d["regime"] = d.regime.fillna(0).astype(int)
        d["other_share"] = d.other_share.fillna(d.other_share.mean())
        d = d[d[x].notna()].copy()
        return d

    def treat(d):
        return d.cyber * d.z * ((d.year - 2017) if model == 1 else (d.year >= 2023).astype(int))

    out = {"break_states": sorted(break_states), "n_break_states": len(break_states)}
    d = sample()
    d = d[~d.state.isin(break_states)].copy()
    d["z"] = standardise(d, x); d["treat"] = treat(d)
    out["drop_break_states"] = coef(fit(d, "treat"), "treat")
    out["drop_break_states"]["states"] = int(d.state.nunique())
    d = sample()
    d["z"] = standardise(d, x); d["treat"] = treat(d)
    d["scr"] = d.sc.astype(str) + "|r" + d.regime.astype(str)  # State x category x recording regime
    out["regime_fixed_effects"] = coef(fit(d, "treat", fe="scr + st + ct"), "treat")
    d["cyber_other_share"] = d.cyber * d.other_share
    out["control_other_share"] = coef(fit(d, "treat + cyber_other_share"), "treat")
    d["cyber_it_share"] = d.cyber * d.it_share.fillna(d.it_share.mean())
    out["all_controls"] = coef(fit(d, "treat + cyber_other_share + cyber_it_share", fe="scr + st + ct"), "treat")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=PANEL)
    ap.add_argument("--out", default="analysis/models")
    ap.add_argument("--perms", type=int, default=300)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    p = pd.read_csv(a.panel)

    m1, ev1 = run_model1(p, a.perms)
    m2, ev2 = run_model2(p, a.perms)
    ev1.to_csv(os.path.join(a.out, "model1_event_study.csv"), index_label="year")
    for x, ev in ev2.items():
        ev.to_csv(os.path.join(a.out, f"model2_event_study_{x}.csv"), index_label="year")
    m1["labelling_controls"] = run_labelling(p, 1)
    m2["labelling_controls"] = run_labelling(p, 2)
    res = {"model1": m1, "model2": m2, "ri_permutations": a.perms}
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=1))
    print("\nModel 1 event study\n", ev1.round(3))
    for x, ev in ev2.items():
        print(f"\nModel 2 event study ({x})\n", ev.round(3))


if __name__ == "__main__":
    main()
