"""Collect every dataset needed for Parts 1-3 into stata/ as Stata .dta files.

Usage: python scripts/build_stata_folder.py   (run after build_analysis_panels.py and funnel_figure.py)

Copies the analysis panels and builds three small extra files:
    labelling_breaks.dta   State x year NCRB labelling breaks (Part 2, labelling controls)
    national_year.dta      India yearly: internet users, NCRB counts, platform complaints, news incidents (Parts 1, 3)
    funnel_2023_2024.dta   reporting-chain stages, 2023 and 2024 (Part 3)
See stata/README.md.
"""
import os, sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from estimate_models import labelling_breaks  # noqa: E402
from export_stata import stata_names  # noqa: E402

OUT = "stata"
ACCESS = "data/external/internet_access/india_internet_access_by_state_age_gender.xlsx"
COPY = {
    "state_category_year_panel": "data/analysis/state_category_year_panel.csv",
    "state_year_panel": "data/analysis/state_year_panel.csv",
    "state_access": "data/analysis/state_access.csv",
    "platform_month_panel": "data/analysis/platform_month_panel.csv",
    "news_incidents_state_year": "data/news/news_incidents_state_year.csv",
    "funnel_2023_2024": "analysis/funnel/funnel_2023_2024.csv",
    "state_controls": "data/analysis/state_controls.csv",
    "state_police": "data/analysis/state_police.csv",
    "state_police_year": "data/analysis/state_police_year.csv",
}
NCRB = ["cyber_vaw_cases", "cyber_vaw_obscene_material", "cyber_vaw_morphing", "cyber_vaw_blackmail",
        "cyber_vaw_stalking", "cyber_vaw_fake_profile", "cyber_vaw_other", "offline_vaw_cases",
        "women_total_cases", "cyber_total_cases", "cyber_fraud"]


def write_dta(d, name):
    names = stata_names(d.columns)
    d = d.rename(columns=names)
    for c in d.columns:
        if d[c].dtype == object:
            d[c] = d[c].fillna("").astype(str)
    d.to_stata(os.path.join(OUT, f"{name}.dta"), write_index=False, version=118,
               variable_labels={new: old[:80] for old, new in names.items()})
    print(f"{name}.dta  {len(d)} rows x {d.shape[1]} cols")


def national_year():
    sy = pd.read_csv("data/analysis/state_year_panel.csv")
    n = sy.groupby("year")[NCRB].sum(min_count=1).reset_index()
    wb = pd.read_excel(ACCESS, "WorldBank_National", header=3)
    wb = wb.rename(columns={wb.columns[0]: "year", wb.columns[1]: "internet_users_pct"})
    n = n.merge(wb[["year", "internet_users_pct", "internet_users_mn"]], on="year", how="outer")

    pm = pd.read_csv("data/analysis/platform_month_panel.csv")
    pm = pm[pm.suspect_duplicate == 0].copy()
    pm["year"] = pm.month.str[:4].astype(int)
    pm["plat"] = pm.platform.str.lower().replace({"facebook": "fb", "instagram": "ig", "snapchat": "snap"})
    pm.loc[pm.platform.isin(["Facebook", "Instagram"]), "plat2"] = "meta"
    wide = []
    for key, d in list(pm.groupby("plat")) + list(pm.dropna(subset=["plat2"]).groupby("plat2")):
        g = d.groupby("year")
        w = pd.DataFrame({f"{key}_all": g["count"].sum(), f"{key}_months": g.month.nunique()})
        for grp in ["sexual", "synthetic"]:
            if (d.category_group == grp).any():
                w[f"{key}_{grp}"] = d[d.category_group == grp].groupby("year")["count"].sum()
        wide.append(w)
    plat = pd.concat(wide, axis=1).reset_index()
    plat["meta_sexual_share_pct"] = (plat.meta_sexual / plat.meta_all * 100).round(2)
    n = n.merge(plat, on="year", how="outer")

    news = pd.read_csv("data/news/news_incidents_state_year.csv")
    news = news.groupby("year")[["ai_deepfake", "morphed", "real_or_unspecified", "all_incidents"]].sum()
    news = news.add_prefix("news_").reset_index()
    n = n.merge(news, on="year", how="outer")
    return n[n.year.between(2012, 2026)].sort_values("year").reset_index(drop=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, path in COPY.items():
        write_dta(pd.read_csv(path, low_memory=False), name)
    br = labelling_breaks()
    write_dta(br[["state", "year", "it_share", "other_share", "brk", "regime"]].rename(columns={"brk": "label_break"}),
              "labelling_breaks")
    write_dta(national_year(), "national_year")


if __name__ == "__main__":
    main()
