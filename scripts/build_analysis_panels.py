"""Build the three analysis panels for the paper on technology shocks and cyber crime against women.

Usage:
    python scripts/build_analysis_panels.py            # defaults below
    python scripts/build_analysis_panels.py --trends data/external/google_trends

Inputs
    data/clean/state_women_cyber_panel.csv          NCRB, State/UT x year (crimes against women, cyber crime)
    data/clean/state_cyber_sexual_abusive.csv       NCRB, sexual/abusive cyber crime, incl. cyber crimes vs women by head
    data/clean/cyber_motives.csv                    NCRB, cyber crime by motive
    data/clean/platform_grievances_monthly.csv      IT Rules grievance reports, platform x category x month
    data/external/internet_access/india_internet_access_by_state_age_gender.xlsx
                                                    NSS 2017-18, NFHS-5, CAMS 2022-23, TRAI subscriptions
    data/external/google_trends/{state_yearly,national_monthly}.csv   optional; merged if present

Outputs (data/analysis/)
    state_year_panel.csv            1. one row per State/UT x year, 2012-2024
    state_category_year_panel.csv   2. one row per State/UT x crime category x year, 2017-2024
    platform_month_panel.csv        3. one row per platform x grievance category x month
    state_access.csv                internet access measures, one row per State/UT (merged into 1 and 2)
    build_report.txt                row counts and coverage checks

Units: boundary changes are merged for the whole period, as in scripts/partB_estimate.py:
D&N Haveli + Daman & Diu, and Jammu & Kashmir + Ladakh, giving 35 State/UT units for 2017-2024.
Counts are summed; rates are recomputed from the summed counts and populations.
"""
import argparse, os, sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from ncrb_tables import clean_state  # noqa: E402

ACCESS_XLSX = "data/external/internet_access/india_internet_access_by_state_age_gender.xlsx"

# Cyber crimes against women by head (NCRB Table 9A.10), 2017-2024.
CYBER_WOMEN = {
    "vs_women_pornography_obscene_material": "obscene material",
    "vs_women_defamation_morphing": "defamation/morphing",
    "vs_women_blackmail_threatening": "blackmail/threatening",
    "vs_women_stalking_bullying": "stalking/bullying",
    "vs_women_fake_profile": "fake profile",
    "vs_women_other": "other cyber vs women",
}
# Heads most exposed to AI image tools (nudify apps, deepfakes): image-based abuse.
AI_SUSCEPTIBLE = {"obscene material", "defamation/morphing", "blackmail/threatening"}
# Offline crimes against women: same victims and police, little exposure to online tools.
OFFLINE_WOMEN = {
    "cruelty_by_husband_or_relatives": "cruelty by husband/relatives",
    "dowry_deaths": "dowry deaths",
    "kidnapping_abduction_of_women": "kidnapping & abduction of women",
    "assault_outrage_modesty_354_incl_354a_d": "assault on modesty (354 incl. A-D)",
    "insult_to_modesty_509": "insult to modesty (509)",
}
# Placebo: online crime that is not targeted at women.
PLACEBO = {"cyber_fraud": "cyber fraud"}

PERIODS = {  # name: (first year, last year), inclusive
    "post_jio": (2017, 2100),     # Jio launched Sep 2016; 2017 is the first full year after
    "post_portal": (2019, 2100),  # National Cyber Crime Reporting Portal, Aug 2019
    "covid": (2020, 2020),
    "post_ai": (2023, 2100),      # generative-AI image tools widely available from late 2022
    "bns": (2024, 2100),          # new criminal code (BNS) replaces IPC from July 2024
}


def merge_units(df, sum_cols, keys=("state", "year")):
    df = df.copy()
    df["state"] = df.state.map(norm_state)
    return df.groupby(list(keys), as_index=False)[sum_cols].sum(min_count=1)


def add_periods(df, year_col="year"):
    for name, (a, b) in PERIODS.items():
        df[name] = df[year_col].between(a, b).astype(int)
    return df


MERGE = {"D&N Haveli": "D&N Haveli and Daman & Diu", "Daman & Diu": "D&N Haveli and Daman & Diu",
         "Ladakh": "Jammu & Kashmir"}
OTHER_NAMES = {"Andaman and Nicobar Islands": "A&N Islands", "NCT of Delhi": "Delhi",
               "National Capital Territory of Delhi": "Delhi", "Orissa": "Odisha"}


def norm_state(s):
    """One name per State/UT unit, merging boundary changes (same rule as scripts/partB_estimate.py)."""
    s = OTHER_NAMES.get(s, s)
    s = clean_state(s.replace(" and ", " & "))
    if "Haveli" in s or "Daman" in s:
        return "D&N Haveli and Daman & Diu"
    return MERGE.get(s, s)


VAW_NAMES = {
    "vs_women_pornography_obscene_material": "cyber_vaw_obscene_material",
    "vs_women_defamation_morphing": "cyber_vaw_morphing",
    "vs_women_blackmail_threatening": "cyber_vaw_blackmail",
    "vs_women_stalking_bullying": "cyber_vaw_stalking",
    "vs_women_fake_profile": "cyber_vaw_fake_profile",
    "vs_women_other": "cyber_vaw_other",
    "vs_women_sexual_intercourse_by_deceit": "cyber_vaw_deceit_bns69",  # new BNS offence, 2024 only
}


# ---------------------------------------------------------------- internet access (one row per state)
def access_measures(path):
    long = pd.read_excel(path, "Survey_Data_Long")
    long = long[long.state != "All India"]

    def pick(survey, indicator, age, gender="Total", sector="Total"):
        d = long[(long.survey == survey) & (long.indicator == indicator) & (long.age_group == age)
                 & (long.gender == gender) & (long.sector == sector)]
        return d.set_index("state")["value_pct"]

    a = pd.DataFrame({
        "access_nss2017_5plus": pick("NSS 75th round", "used internet in last 30 days", "5+"),
        "access_cams2023_15plus": pick("CAMS (NSS 79th round)", "used internet in last 3 months", "15+"),
        "access_cams2023_15to24": pick("CAMS (NSS 79th round)", "used internet in last 3 months", "15-24"),
        "able_cams2023_15plus": pick("CAMS (NSS 79th round)", "able to use internet", "15+"),
    })
    nf = (pick("NFHS-5", "ever used internet", "15-49", "Male") + pick("NFHS-5", "ever used internet", "15-49", "Female")) / 2
    a["access_nfhs5_15to49_avg"] = nf

    # TRAI subscriptions per 100 people (connections, not people), December of each year.
    raw = pd.read_excel(path, "TRAI_State_Subs", header=None)
    hdr_block, hdr_date = raw.iloc[3].ffill(), raw.iloc[4]
    body = raw.iloc[5:].copy()
    body = body[body[0].notna() & (body[0] != "All India")]
    trai = {}
    for col in range(1, raw.shape[1]):
        block, date = str(hdr_block[col]), str(hdr_date[col])
        if not date.endswith("-12"):
            continue
        if block.startswith("Total subscriptions"):
            trai[("subs_mn", int(date[:4]))] = pd.to_numeric(body[col], errors="coerce").values
        elif block.startswith("Per 100"):
            trai[("per100", int(date[:4]))] = pd.to_numeric(body[col], errors="coerce").values
    t = pd.DataFrame(trai, index=body[0].values)
    t.columns = pd.MultiIndex.from_tuples(t.columns)

    # Merge boundary units: survey percentages population-weighted with NCRB population, TRAI from counts.
    pop = load_population()
    a["unit"] = [norm_state(s) for s in a.index]
    a["w"] = [pop.get(s, np.nan) for s in a.index]
    out = {}
    for unit, g in a.groupby("unit"):
        row = {}
        for c in [c for c in a.columns if c.startswith(("access_", "able_"))]:
            v = g[[c, "w"]].dropna()
            if len(v) == 0:
                row[c] = np.nan
            elif len(v) == 1 or v.w.isna().any():
                row[c] = v[c].iloc[0] if len(v) == 1 else v[c].mean()
            else:
                row[c] = np.average(v[c], weights=v.w)
        out[unit] = row
    acc = pd.DataFrame(out).T

    t["unit"] = [norm_state(s) for s in t.index]
    years = sorted({y for k, y in t.columns if k == "per100"})
    for y in years:
        implied_pop = t[("subs_mn", y)] * 100 / t[("per100", y)]
        tmp = pd.DataFrame({"subs": t[("subs_mn", y)], "pop": implied_pop, "unit": t["unit"]})
        g = tmp.groupby("unit").sum(min_count=1)
        acc[f"trai_subs_per100_{y}"] = (g.subs * 100 / g["pop"]).round(2)
    acc.index.name = "state"
    return acc.round(2)


def load_population():
    """Population (lakh) by original NCRB State/UT name, 2022, for weighting merged units."""
    w = pd.read_csv("data/clean/state_women_cyber_panel.csv")
    w = w[(w.row_type == "state_ut") & (w.year == 2022)]
    return dict(zip(w.state, w.population_lakh))


def trai_long(acc):
    cols = [c for c in acc.columns if c.startswith("trai_subs_per100_")]
    t = acc[cols].reset_index().melt(id_vars="state", var_name="v", value_name="trai_subs_per100")
    t["year"] = t.v.str[-4:].astype(int)
    t.loc[t.year == 2021, "trai_subs_per100"] = np.nan  # TRAI's Dec 2021 State split misallocates several States
    return t.drop(columns="v")


# ---------------------------------------------------------------- Google Trends (optional)
def trends_state_year(trends_dir):
    f = os.path.join(trends_dir, "state_yearly.csv")
    if not os.path.exists(f):
        return None
    t = pd.read_csv(f)
    t["state"] = t.state.map(norm_state)
    t = t.groupby(["state", "year", "group"], as_index=False)["value"].mean()
    t = t.pivot_table(index=["state", "year"], columns="group", values="value").reset_index()
    t.columns = ["state", "year"] + [f"trends_{c}" for c in t.columns[2:]]
    return t


def trends_national_month(trends_dir):
    f = os.path.join(trends_dir, "national_monthly.csv")
    if not os.path.exists(f):
        return None
    t = pd.read_csv(f)
    date_col = "month" if "month" in t.columns else "date"
    t["month"] = pd.to_datetime(t[date_col]).dt.strftime("%Y-%m")
    t = t.groupby(["month", "group"], as_index=False)["value"].mean()
    t = t.pivot(index="month", columns="group", values="value").reset_index()
    t.columns = ["month"] + [f"trends_national_{c}" for c in t.columns[1:]]
    return t


# ---------------------------------------------------------------- 1. state x year
def state_year(clean, acc, trends):
    w = pd.read_csv(os.path.join(clean, "state_women_cyber_panel.csv"))
    c = pd.read_csv(os.path.join(clean, "state_cyber_sexual_abusive.csv"))
    w, c = w[w.row_type == "state_ut"], c[c.row_type == "state_ut"]

    wcols = ["women_total_cases", "female_population_lakh", "population_lakh", "cyber_total_cases",
             "cyber_crimes_against_women", "cyber_crimes_against_children", "cyber_fraud",
             "women_centric_cyber_crimes"] + list(OFFLINE_WOMEN)
    ccols = ["sexual_content_total", "sexual_abusive_total"] + list(VAW_NAMES)
    p = merge_units(w, wcols).merge(merge_units(c, ccols), on=["state", "year"], how="left")

    # Chargesheeting rate: cases-weighted average across merged units.
    cs = w[["state", "year", "cyber_chargesheeting_rate", "cyber_total_cases"]].copy()
    cs["state"] = cs.state.map(norm_state)
    cs["num"] = cs.cyber_chargesheeting_rate * cs.cyber_total_cases
    cs = cs.dropna(subset=["num"]).groupby(["state", "year"], as_index=False)[["num", "cyber_total_cases"]].sum()
    cs["cyber_chargesheet_rate"] = (cs.num / cs.cyber_total_cases).round(1)
    p = p.merge(cs[["state", "year", "cyber_chargesheet_rate"]], on=["state", "year"], how="left")

    # Motive: sexual exploitation (State level 2018-2024).
    m = pd.read_csv(os.path.join(clean, "cyber_motives.csv"))
    m = m[(m.row_type == "state_ut") & (m.motive_group == "Sexual exploitation")]
    m = merge_units(m.rename(columns={"cases": "cyber_motive_sexual_exploitation"}), ["cyber_motive_sexual_exploitation"])
    p = p.merge(m, on=["state", "year"], how="left")

    p = p.rename(columns={"cyber_crimes_against_women": "cyber_vaw_cases", "female_population_lakh": "female_pop_lakh",
                          **VAW_NAMES})
    p["offline_vaw_cases"] = p[list(OFFLINE_WOMEN)].sum(axis=1, min_count=len(OFFLINE_WOMEN))
    p = p.drop(columns=list(OFFLINE_WOMEN))

    per_women = {"cyber_vaw_cases": "cyber_vaw_rate", "offline_vaw_cases": "offline_vaw_rate",
                 "women_total_cases": "women_crime_rate"}
    per_pop = {"cyber_total_cases": "cyber_total_rate", "cyber_fraud": "cyber_fraud_rate",
               "sexual_content_total": "sexual_content_rate"}
    for k, v in per_women.items():
        p[v] = (p[k] / p.female_pop_lakh).round(3)
    for k, v in per_pop.items():
        p[v] = (p[k] / p.population_lakh).round(3)

    p = p.merge(acc.drop(columns=[c for c in acc.columns if c.startswith("trai_")]), left_on="state", right_index=True, how="left")
    p = p.merge(trai_long(acc), on=["state", "year"], how="left")
    if trends is not None:
        p = p.merge(trends, on=["state", "year"], how="left")
    p = add_periods(p)
    return p.sort_values(["state", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------- 2. state x category x year
def state_category_year(clean, acc, trends):
    w = pd.read_csv(os.path.join(clean, "state_women_cyber_panel.csv"))
    c = pd.read_csv(os.path.join(clean, "state_cyber_sexual_abusive.csv"))
    w, c = w[w.row_type == "state_ut"], c[c.row_type == "state_ut"]
    rows = []
    for df, cats, group in ((c, CYBER_WOMEN, "cyber_women"), (w, OFFLINE_WOMEN, "offline_women"), (w, PLACEBO, "cyber_placebo")):
        for col, label in cats.items():
            d = df[["state", "year", col]].dropna().rename(columns={col: "cases"})
            d["category"], d["category_group"] = label, group
            rows.append(d)
    p = pd.concat(rows)
    p = p[p.year.between(2017, 2024)]
    p["state"] = p.state.map(norm_state)
    p = p.groupby(["state", "year", "category", "category_group"], as_index=False)["cases"].sum()

    pop = merge_units(w, ["female_population_lakh", "population_lakh"])
    p = p.merge(pop.rename(columns={"female_population_lakh": "female_pop_lakh"}), on=["state", "year"], how="left")
    p["is_cyber_vaw"] = (p.category_group == "cyber_women").astype(int)
    p["is_ai_susceptible"] = p.category.isin(AI_SUSCEPTIBLE).astype(int)
    p["is_placebo"] = (p.category_group == "cyber_placebo").astype(int)
    p = p.merge(acc.drop(columns=[c for c in acc.columns if c.startswith("trai_")]), left_on="state", right_index=True, how="left")
    p = p.merge(trai_long(acc), on=["state", "year"], how="left")
    if trends is not None:
        p = p.merge(trends, on=["state", "year"], how="left")
    p = add_periods(p)
    return p.sort_values(["state", "category", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------- 3. platform x category x month
EVENTS = {  # month ranges, inclusive
    "grok2_images": ("2024-08", "2024-11"),       # Grok-2 image generation for X Premium users
    "grok_free": ("2024-12", "2025-02"),          # Grok + Aurora image model free for all X users
}


def platform_month(clean, trends_nat):
    g = pd.read_csv(os.path.join(clean, "platform_grievances_monthly.csv"))
    g = g.rename(columns={"group": "category_group"})
    g["is_synthetic_media"] = (g.category_group == "synthetic").astype(int)
    g["is_sexual_content"] = (g.category_group == "sexual").astype(int)
    g["is_placebo"] = (g.category_group == "placebo").astype(int)
    for name, (a, b) in EVENTS.items():
        g[name] = g.month.between(a, b).astype(int)
    g["post_grok_free"] = (g.month >= "2024-12").astype(int)
    if trends_nat is not None:
        g = g.merge(trends_nat, on="month", how="left")
    return g.sort_values(["platform", "category", "month"]).reset_index(drop=True)


def coverage(df, cols, by="year"):
    return df.groupby(by)[cols].apply(lambda d: d.notna().sum()).to_string()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", default="data/clean")
    ap.add_argument("--access", default=ACCESS_XLSX)
    ap.add_argument("--trends", default="data/external/google_trends")
    ap.add_argument("--out", default="data/analysis")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    acc = access_measures(a.access)
    trends, trends_nat = trends_state_year(a.trends), trends_national_month(a.trends)
    sy = state_year(a.clean, acc, trends)
    scy = state_category_year(a.clean, acc, trends)
    pm = platform_month(a.clean, trends_nat)

    acc.to_csv(os.path.join(a.out, "state_access.csv"))
    sy.to_csv(os.path.join(a.out, "state_year_panel.csv"), index=False)
    scy.to_csv(os.path.join(a.out, "state_category_year_panel.csv"), index=False)
    pm.to_csv(os.path.join(a.out, "platform_month_panel.csv"), index=False)

    rep = [
        f"state_year_panel: {len(sy)} rows, {sy.state.nunique()} units, {sy.year.min()}-{sy.year.max()}",
        f"state_category_year_panel: {len(scy)} rows, {scy.state.nunique()} units, {scy.category.nunique()} categories",
        f"platform_month_panel: {len(pm)} rows, platforms {sorted(pm.platform.unique())}, {pm.month.min()} to {pm.month.max()}",
        f"Google Trends merged: {'yes' if trends is not None else 'NO - data/external/google_trends/state_yearly.csv not found'}",
        "", "Units with no NCRB match in access data:", str(sorted(set(sy.state) - set(acc.index))),
        "Access units with no NCRB match:", str(sorted(set(acc.index) - set(sy.state))),
        "", "Non-missing values by year (state_year_panel):",
        coverage(sy, ["cyber_vaw_cases", "offline_vaw_cases", "cyber_total_cases", "cyber_fraud", "female_pop_lakh",
                      "cyber_chargesheet_rate", "cyber_motive_sexual_exploitation", "trai_subs_per100"]),
        "", "Access measures, non-missing units:", acc.notna().sum().to_string(),
    ]
    with open(os.path.join(a.out, "build_report.txt"), "w") as f:
        f.write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
