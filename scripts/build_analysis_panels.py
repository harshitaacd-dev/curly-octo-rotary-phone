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
    data/external/google_trends/{panel_state_yearly,keyword_volumes,national_monthly}.csv
                                                    Google Trends and Google Ads search data; merged if present

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


# ---------------------------------------------------------------- Google Trends and Google Ads search volumes
# Inputs in data/external/google_trends/ (see datasets/README.md, section 4):
#   panel_state_yearly.csv   State x year x concept, Trends index linked across States (2018-2026)
#   keyword_volumes.csv      State (and India) x keyword x month, Google Ads volumes (Nov 2022 - Sep 2026)
#   national_monthly.csv     India x month x concept, estimated searches (2018-2026)
CONCEPTS = ["deepfake_awareness", "deepfake_explainer", "deepfake_apps", "deepfake_apk", "deepfake_free",
            "deepfake_makers", "face_swap", "face_swap_video", "reface"]
# Google Ads keyword groups. Volumes are Google's rounded monthly buckets; summed within group.
KEYWORD_GROUPS = {
    "nudify": ["cloth remover app", "clothoff", "clothoff app", "deepnude", "deepnude app", "dress remover app",
               "kapde utarne wala app", "nakedly", "nakedly ai", "nangi photo app", "nudeai", "nudeai fun",
               "nudify app", "nudify bot", "nudify online", "photo se kapde hatane wala app", "telegram nude bot",
               "undress app", "undress bot telegram", "grok undress"],
    "grok_sexual": ["grok bikini", "grok spicy mode"],
    "help_seeking": ["cyber crime complaint", "deepfake complaint", "how to report deepfake", "stopncii",
                     "deepfake law india"],
    "genai": ["ai image generator", "ai video generator", "ai photo editor", "grok", "grok ai", "grok image",
              "grok imagine"],
}
PRE_AI_YEARS = (2018, 2022)   # Trends exposure measured before the generative-AI boom
POST_AI_YEARS = (2023, 2024)  # Ads volumes: first full years with data, inside the crime panel


def _weighted_unit_mean(df, value_cols, pop):
    """Average original Trends regions into merged units, weighted by 2022 population where known."""
    df = df.copy()
    df["unit"] = df.state.map(norm_state)
    df["w"] = df.state.map(lambda s: pop.get(clean_state(s.replace(" and ", " & ")), np.nan)).fillna(1.0)
    keys = [c for c in df.columns if c not in value_cols + ["state", "w", "unit"]]
    out = df.groupby(["unit"] + keys).apply(
        lambda g: pd.Series({c: np.average(g[c].dropna(), weights=g.loc[g[c].notna(), "w"]) if g[c].notna().any() else np.nan
                             for c in value_cols}), include_groups=False).reset_index()
    return out.rename(columns={"unit": "state"})


def trends_state_year(trends_dir):
    f = os.path.join(trends_dir, "panel_state_yearly.csv")
    if not os.path.exists(f):
        return None
    t = pd.read_csv(f)
    t = t[t.months == 12]  # full years only (2026 is partial)
    wide = t.pivot_table(index=["state", "year"], columns="concept", values="panel_index_mean").reset_index()
    low = t.pivot_table(index=["state", "year"], columns="concept", values="low_precision", aggfunc="max")
    wide["trends_low_precision_n"] = low.sum(axis=1).values
    wide = wide.rename(columns={c: f"trends_{c}" for c in CONCEPTS})
    vals = [c for c in wide.columns if c.startswith("trends_")]
    return _weighted_unit_mean(wide, vals, load_population()).round(3)


def ads_state_year(trends_dir):
    f = os.path.join(trends_dir, "keyword_volumes.csv")
    if not os.path.exists(f):
        return None
    k = pd.read_csv(f)
    k = k[k.location != "India"]
    group_of = {kw: g for g, kws in KEYWORD_GROUPS.items() for kw in kws}
    k["group"] = k.keyword.map(group_of)
    k = k.dropna(subset=["group"])
    k["year"] = k.month.str[:4].astype(int)
    months = k.groupby("year").month.nunique()
    k = k[k.year.isin(months[months == 12].index)]  # full years only
    k["state"] = k.location.map(norm_state)
    a = k.groupby(["state", "year", "group"], as_index=False)["google_ads_monthly_searches"].sum()
    a = a.pivot_table(index=["state", "year"], columns="group", values="google_ads_monthly_searches").reset_index()
    a.columns = ["state", "year"] + [f"ads_{c}_searches" for c in a.columns[2:]]
    return a


def ads_national_month(trends_dir):
    f = os.path.join(trends_dir, "keyword_volumes.csv")
    if not os.path.exists(f):
        return None
    k = pd.read_csv(f)
    k = k[k.location == "India"]
    group_of = {kw: g for g, kws in KEYWORD_GROUPS.items() for kw in kws}
    k["group"] = k.keyword.map(group_of)
    a = k.dropna(subset=["group"]).groupby(["month", "group"], as_index=False)["google_ads_monthly_searches"].sum()
    a = a.pivot(index="month", columns="group", values="google_ads_monthly_searches").reset_index()
    a.columns = ["month"] + [f"ads_national_{c}_searches" for c in a.columns[1:]]
    return a


def trends_national_month(trends_dir):
    f = os.path.join(trends_dir, "national_monthly.csv")
    if not os.path.exists(f):
        return None
    t = pd.read_csv(f)
    t = t.pivot(index="month", columns="concept", values="estimated_searches").reset_index()
    t.columns = ["month"] + [f"trends_national_{c}" for c in t.columns[1:]]
    nat_ads = ads_national_month(trends_dir)
    if nat_ads is not None:
        t = t.merge(nat_ads, on="month", how="outer")
    return t.sort_values("month")


def search_exposure(trends_sy, ads_sy, pop_sy):
    """Fixed, one-per-State exposure measures from search data."""
    e = pd.DataFrame()
    if trends_sy is not None:
        pre = trends_sy[trends_sy.year.between(*PRE_AI_YEARS)]
        for c in ["trends_deepfake_awareness", "trends_face_swap", "trends_deepfake_apps", "trends_reface"]:
            e[f"{c}_pre"] = pre.groupby("state")[c].mean()
    if ads_sy is not None:
        post = ads_sy[ads_sy.year.between(*POST_AI_YEARS)].merge(pop_sy, on=["state", "year"], how="left")
        for g in KEYWORD_GROUPS:
            col = f"ads_{g}_searches"
            if col in post:
                post[f"r_{g}"] = post[col] / post.population_lakh
                e[f"ads_{g}_per_lakh_post"] = post.groupby("state")[f"r_{g}"].mean()
        if {"ads_nudify_searches", "ads_genai_searches"} <= set(post.columns):
            tot = post.groupby("state")[["ads_nudify_searches", "ads_genai_searches"]].sum()
            # Interest in abuse tools relative to general AI-tool interest (separates abuse demand from connectivity).
            e["ads_nudify_to_genai_post"] = tot.ads_nudify_searches / tot.ads_genai_searches
    e.index.name = "state"
    return e.round(3)


# ---------------------------------------------------------------- 1. state x year
def state_year(clean, acc, trends, ads):
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
    if ads is not None:
        p = p.merge(ads, on=["state", "year"], how="left")
        for c in [c for c in ads.columns if c.endswith("_searches")]:
            p[c.replace("_searches", "_per_lakh")] = (p[c] / p.population_lakh).round(3)
    p = add_periods(p)
    return p.sort_values(["state", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------- 2. state x category x year
def state_category_year(clean, acc, trends):
    """Search data enters this panel only as fixed State exposure (via acc); yearly Trends columns are merged too."""
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


SNAP = "data/external/platform_reports/snap.csv"
SHARECHAT = "data/external/platform_reports/sharechat.csv"


def snap_month(path=SNAP):
    """Snapchat user reports (content & account reports) by month: sexual content, harassment, other.

    Joins three report formats: 'Sexually Explicit Content' (Dec 2021 - Dec 2022), 'Sexual Content'
    (Jan 2023 - Nov 2024), and the 'reported to safety teams' section (Dec 2024 onwards).
    Nov 2025 repeats Oct 2025 exactly in every category (a duplicated report in the source), so it is
    flagged suspect_duplicate = 1.
    """
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    d = d[(d.metric == "content & account reports") & d.unit.str.startswith("count")
          & d.section.isin(["reports and enforcement", "reported to safety teams"])]
    d["cat"] = d.category.replace({"Sexually Explicit Content": "sexual", "Sexual Content": "sexual",
                                   "Harassment and Bullying": "harassment", "All": "all"})
    d = d[d.cat.isin(["sexual", "harassment", "all"])]
    w = d.pivot_table(index="period_start", columns="cat", values="value", aggfunc="sum")
    w.index = w.index.str[:7]
    w["other"] = w["all"] - w[["sexual", "harassment"]].sum(axis=1, min_count=2)
    rows = []
    for col, label, group in (("sexual", "Sexual content", "sexual"), ("harassment", "Harassment and bullying", "harassment"),
                              ("other", "All other reasons", "placebo")):
        r = w[[col]].dropna().reset_index().rename(columns={"period_start": "month", col: "count"})
        r["platform"], r["category"], r["category_group"], r["derived_from_share"] = "Snapchat", label, group, False
        rows.append(r)
    out = pd.concat(rows, ignore_index=True)
    dup = w[["all", "sexual", "harassment"]].diff().abs().sum(axis=1) == 0
    out["suspect_duplicate"] = out.month.isin(w.index[dup]).astype(int)
    return out


SHARECHAT_GROUPS = {"Sexually explicit content": "sexual", "Abusive language": "harassment",
                    "Fake profile": "impersonation", "Impersonation": "impersonation"}


def sharechat_month(path=SHARECHAT):
    """ShareChat and Moj user reports by month (June 2021 - October 2022; their public reports stop there).

    From scripts/sharechat_parse.py. Groups: sexually explicit content, abusive language (harassment),
    fake profile + impersonation, and all other reasons (placebo). All reports = sum of the reasons when
    they add to about 100%. November 2021 lists only some reasons, so its "all other reasons" row is left
    out. The stated total is not used because July 2022 repeats June 2022's total in the source.
    """
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    d["grp"] = d.reason.map(SHARECHAT_GROUPS).fillna("placebo")
    rows = []
    for (app, month), m in d.groupby(["app", "month"]):
        full = m.share_pct.sum() > 95
        total = m["count"].sum() if full else m.total_reports.iloc[0]
        derived = bool(m.derived_from_share.max())
        named = {}
        for grp, label in (("sexual", "Sexually explicit content"), ("harassment", "Abusive language"),
                           ("impersonation", "Fake profile or impersonation")):
            if (m.grp == grp).any():
                named[grp] = m.loc[m.grp == grp, "count"].sum()
                rows.append((app, label, grp, month, named[grp], derived))
        if full:  # Nov 2021 lists only some reasons, so "all other reasons" is unknown that month
            rows.append((app, "All other reasons", "placebo", month, total - sum(named.values()), derived))
    out = pd.DataFrame(rows, columns=["platform", "category", "category_group", "month", "count", "derived_from_share"])
    out["suspect_duplicate"] = 0
    return out


def platform_month(clean, trends_nat):
    g = pd.read_csv(os.path.join(clean, "platform_grievances_monthly.csv"))
    g = g.rename(columns={"group": "category_group"})
    g["suspect_duplicate"] = 0
    snap = snap_month()
    if snap is not None:
        g = pd.concat([g, snap[g.columns]], ignore_index=True)
    sc = sharechat_month()
    if sc is not None:
        g = pd.concat([g, sc[g.columns]], ignore_index=True)
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
    trends, ads, trends_nat = trends_state_year(a.trends), ads_state_year(a.trends), trends_national_month(a.trends)
    w = pd.read_csv(os.path.join(a.clean, "state_women_cyber_panel.csv"))
    pop_sy = merge_units(w[w.row_type == "state_ut"], ["population_lakh"])
    acc = acc.join(search_exposure(trends, ads, pop_sy), how="left")
    sy = state_year(a.clean, acc, trends, ads)
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
        f"  Snapchat months flagged suspect_duplicate: {sorted(pm[pm.suspect_duplicate == 1].month.unique())}",
        f"Google Trends State panel merged: {'yes' if trends is not None else 'NO (panel_state_yearly.csv not found)'}",
        f"Google Ads keyword volumes merged: {'yes' if ads is not None else 'NO (keyword_volumes.csv not found)'}",
        "", "Units with no NCRB match in access data:", str(sorted(set(sy.state) - set(acc.index))),
        "NCRB units with no Trends data:", str(sorted(set(sy.state) - set(trends.state))) if trends is not None else "",
        "Trends units with no NCRB match:", str(sorted(set(trends.state) - set(sy.state))) if trends is not None else "",
        "NCRB units with no Ads data:", str(sorted(set(sy.state) - set(ads.state))) if ads is not None else "",
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
