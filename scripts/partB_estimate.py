"""Part B: did AI-susceptible cyber crimes against women rise more after 2022 in more-exposed states?

Usage:
    python scripts/partB_estimate.py --exposure trends   --trends data/external/google_trends --out analysis/partB
    python scripts/partB_estimate.py --exposure cyberrate --out analysis/partB_cyberrate   (stand-in exposure)

Panel: State/UT x offence category x year, 2017-2024, from data/clean (NCRB).
  AI-susceptible (cyber crimes against women, Table 9A.10): obscene/pornographic material,
      defamation/morphing, fake profile, blackmail/threatening, stalking/bullying
  Comparison (offline crimes against women, Table 3A.2): cruelty by husband/relatives, dowry
      deaths, kidnapping & abduction of women, assault on modesty (Sec 354 incl. 354A-D),
      insult to modesty (Sec 509). Same victims and police, little AI exposure.
Model (Poisson, pyfixest.fepois), standard errors clustered by state:
    count_sct ~ Susceptible_c x Post_t x Exposure_s | state x category + state x year + category x year
  Post = 2023-2024 (generative-AI image tools widely available from late 2022).
  Exposure_s is standardised (mean 0, sd 1), so the coefficient is the extra change in AI-susceptible
  crimes for a state one standard deviation more exposed.
  Event study: Susceptible x Exposure x year dummies, base year 2021.
Boundary changes are merged for the whole period: D&N Haveli + Daman & Diu; Jammu & Kashmir + Ladakh.

Exposure options
  trends     search interest in nudify + deepfake tools by state (Google Trends state_yearly.csv),
             averaged over samples and terms, years 2023-2024 by default (--trend-years)
  cyberrate  stand-in: state cyber crime rate per lakh population, 2017-2021 average
"""
import argparse, json, os, re, sys
import numpy as np
import pandas as pd
import pyfixest as pf

sys.path.insert(0, os.path.dirname(__file__))
from ncrb_tables import clean_state  # noqa: E402

SUSCEPTIBLE = {
    "vs_women_pornography_obscene_material": "obscene material (cyber, women)",
    "vs_women_defamation_morphing": "defamation/morphing (cyber, women)",
    "vs_women_fake_profile": "fake profile (cyber, women)",
    "vs_women_blackmail_threatening": "blackmail/threatening (cyber, women)",
    "vs_women_stalking_bullying": "stalking/bullying (cyber, women)",
}
OFFLINE = {
    "cruelty_by_husband_or_relatives": "cruelty by husband/relatives",
    "dowry_deaths": "dowry deaths",
    "kidnapping_abduction_of_women": "kidnapping & abduction of women",
    "assault_outrage_modesty_354_incl_354a_d": "assault on modesty (354 incl. A-D)",
    "insult_to_modesty_509": "insult to modesty (509)",
}
MERGE = {"D&N Haveli": "D&N Haveli and Daman & Diu", "Daman & Diu": "D&N Haveli and Daman & Diu",
         "Ladakh": "Jammu & Kashmir"}
GOOGLE_NAMES = {  # Google Trends region names -> NCRB names (others go through clean_state)
    "Andaman and Nicobar Islands": "A&N Islands", "NCT of Delhi": "Delhi", "National Capital Territory of Delhi": "Delhi",
    "Dadra and Nagar Haveli and Daman and Diu": "D&N Haveli and Daman & Diu",
    "Dadra and Nagar Haveli": "D&N Haveli", "Daman and Diu": "Daman & Diu", "Orissa": "Odisha",
}


def norm_state(s):
    s = GOOGLE_NAMES.get(s, s)
    s = clean_state(s.replace(" and ", " & "))
    if "Haveli" in s or "Daman" in s:
        return "D&N Haveli and Daman & Diu"
    return MERGE.get(s, s)


def load_panel(clean):
    w = pd.read_csv(os.path.join(clean, "state_women_cyber_panel.csv"))
    c = pd.read_csv(os.path.join(clean, "state_cyber_sexual_abusive.csv"))
    w, c = w[w.row_type == "state_ut"], c[c.row_type == "state_ut"]
    rows = []
    for df, cats, sus in ((c, SUSCEPTIBLE, 1), (w, OFFLINE, 0)):
        for col, label in cats.items():
            d = df[["state", "year", col]].dropna().rename(columns={col: "count"})
            d["category"], d["susceptible"] = label, sus
            rows.append(d)
    p = pd.concat(rows)
    p = p[(p.year >= 2017) & (p.year <= 2024)]
    p["state"] = p.state.map(norm_state)
    p = p.groupby(["state", "year", "category", "susceptible"], as_index=False)["count"].sum()
    return p


def exposure_trends(trends_dir, years, groups=("nudify", "deepfake_tools")):
    t = pd.read_csv(os.path.join(trends_dir, "state_yearly.csv"))
    t = t[t.group.isin(groups) & t.year.isin(years)]
    t["state"] = t.state.map(norm_state)
    e = t.groupby("state")["value"].mean()
    return np.log1p(e)


def exposure_cyberrate(clean):
    w = pd.read_csv(os.path.join(clean, "state_women_cyber_panel.csv"))
    w = w[(w.row_type == "state_ut") & w.year.between(2017, 2021)]
    w["state"] = w.state.map(norm_state)
    g = w.groupby(["state", "year"])[["cyber_total_cases", "population_lakh"]].sum(min_count=1).reset_index()
    g["rate"] = g.cyber_total_cases / g.population_lakh
    return np.log(g.groupby("state")["rate"].mean().replace(0, np.nan)).dropna()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exposure", choices=["trends", "cyberrate"], required=True)
    ap.add_argument("--trends", default="data/external/google_trends")
    ap.add_argument("--trend-years", default="2023,2024")
    ap.add_argument("--clean", default="data/clean")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    p = load_panel(a.clean)
    if a.exposure == "trends":
        e = exposure_trends(a.trends, [int(y) for y in a.trend_years.split(",")])
    else:
        e = exposure_cyberrate(a.clean)
    e = ((e - e.mean()) / e.std()).rename("exposure")
    e.to_csv(os.path.join(a.out, "exposure.csv"))
    p = p.merge(e, left_on="state", right_index=True, how="inner")
    p["post"] = (p.year >= 2023).astype(int)
    p["treat"] = p.susceptible * p.post * p.exposure
    p["sc"], p["st"], p["ct"] = p.state + "|" + p.category, p.state + "|" + p.year.astype(str), p.category + "|" + p.year.astype(str)
    years = sorted(p.year.unique())
    for y in years:
        p[f"es{y}"] = p.susceptible * p.exposure * (p.year == y)
    es_terms = [f"es{y}" for y in years if y != 2021]

    out = {"exposure": a.exposure, "states": int(p.state.nunique()), "obs": int(len(p)),
           "categories": sorted(p.category.unique())}
    m = pf.fepois("count ~ treat | sc + st + ct", data=p, vcov={"CRV1": "state"})
    t = m.tidy().loc["treat"]
    out["main"] = {"coef": round(float(t["Estimate"]), 3), "se": round(float(t["Std. Error"]), 3),
                   "p": round(float(t["Pr(>|t|)"]), 4), "irr_per_sd": round(float(np.exp(t["Estimate"])), 3)}
    ev = pf.fepois("count ~ " + " + ".join(es_terms) + " | sc + st + ct", data=p, vcov={"CRV1": "state"})
    es = ev.tidy().loc[es_terms, ["Estimate", "Std. Error", "Pr(>|t|)"]]
    es.index = [int(i[2:]) for i in es.index]
    es.loc[2021] = [0.0, 0.0, np.nan]
    es = es.sort_index()
    es.to_csv(os.path.join(a.out, "event_study.csv"), index_label="year")
    out["event_study"] = {int(y): {"coef": round(float(r["Estimate"]), 3), "se": round(float(r["Std. Error"]), 3)}
                          for y, r in es.iterrows()}
    # Pre-trend test: joint Wald on 2017-2020 terms
    pre = [f"es{y}" for y in years if y < 2021]
    try:
        wt = ev.wald_test(R=np.eye(len(es_terms))[[es_terms.index(x) for x in pre]])
        out["pretrend_wald_p"] = round(float(np.asarray(wt["pvalue"] if isinstance(wt, dict) else wt.iloc[-1]).ravel()[0]), 4)
    except Exception as ex:
        out["pretrend_wald_p"] = f"not computed ({type(ex).__name__})"
    # Per-category effects
    per = {}
    for cat in sorted(p[p.susceptible == 1].category.unique()):
        d = p[(p.susceptible == 0) | (p.category == cat)]
        try:
            mm = pf.fepois("count ~ treat | sc + st + ct", data=d, vcov={"CRV1": "state"})
            tt = mm.tidy().loc["treat"]
            per[cat] = {"coef": round(float(tt["Estimate"]), 3), "se": round(float(tt["Std. Error"]), 3),
                        "p": round(float(tt["Pr(>|t|)"]), 4)}
        except Exception as ex:
            per[cat] = f"failed ({type(ex).__name__})"
    out["by_category"] = per
    # Robustness: drop 2024 (first BNS year)
    d = p[p.year <= 2023]
    r = pf.fepois("count ~ treat | sc + st + ct", data=d, vcov={"CRV1": "state"}).tidy().loc["treat"]
    out["drop_2024"] = {"coef": round(float(r["Estimate"]), 3), "se": round(float(r["Std. Error"]), 3), "p": round(float(r["Pr(>|t|)"]), 4)}
    with open(os.path.join(a.out, "results.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
