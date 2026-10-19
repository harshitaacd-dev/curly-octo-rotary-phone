"""Parts 1 and 2 with State controls: income per head (log) and urban share.

Usage: python scripts/controls_checks.py   (needs data/analysis/state_controls.csv from build_controls.py;
writes analysis/models/controls_checks.json)

1b  Across States (levels): cases ~ Access + log income + urban share | year, population offset (Poisson).
Model 1 and Model 2: the controls enter like the exposure, interacted with Cyber x (year - 2017) or
Cyber x Post, so they absorb any growth or post-2022 change that tracks income or urbanisation.
All State variables standardised (mean 0, SD 1); 33 States (no RBI income for Lakshadweep and DNH-DD).
"""
import json, os, sys, warnings

import numpy as np
import pandas as pd
import pyfixest as pf

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
from estimate_models import model1_sample  # noqa: E402

CTRL = "data/analysis/state_controls.csv"
OUT = "analysis/models/controls_checks.json"
SETS = {"none": [], "income": ["z_income"], "urban": ["z_urban"], "income_urban": ["z_income", "z_urban"]}


def zcols(d, acc):
    s = d.groupby("state")[[acc, "nsdp_pc_avg", "urban_share_cams"]].first()
    s["nsdp_pc_avg"] = np.log(s.nsdp_pc_avg)
    s = (s - s.mean()) / s.std()
    d["z_access"] = d.state.map(s[acc])
    d["z_income"] = d.state.map(s["nsdp_pc_avg"])
    d["z_urban"] = d.state.map(s["urban_share_cams"])
    return d


def res(m, terms):
    return {t: {"rate_ratio": round(float(np.exp(m.coef()[t])), 3), "p": round(float(m.pvalue()[t]), 4)} for t in terms}


def levels(c):
    sy = pd.read_csv("data/analysis/state_year_panel.csv").merge(c, on="state")
    out = {}
    for y in ["cyber_vaw_cases", "offline_vaw_cases"]:
        d = sy[sy.year.between(2017, 2024)].dropna(subset=["access_cams2023_15plus", y, "nsdp_pc_avg"]).copy()
        d = zcols(d, "access_cams2023_15plus")
        d["lo"] = np.log(d.female_pop_lakh)
        out[y] = {}
        for k, ctrl in SETS.items():
            rhs = " + ".join(["z_access"] + ctrl)
            m = pf.fepois(f"{y} ~ {rhs} | year", data=d, offset="lo", vcov={"CRV1": "state"})
            out[y][k] = res(m, ["z_access"] + ctrl)
    return out


def models(c):
    base = model1_sample(pd.read_csv("data/analysis/state_category_year_panel.csv").merge(c, on="state"), "total")
    out = {}
    for name, acc in [("model1", "access_cams2023_15plus"), ("model2", "access_nfhs5_15to49_avg")]:
        d = zcols(base.dropna(subset=[acc, "nsdp_pc_avg"]).copy(), acc)
        k = (d.year - 2017) if name == "model1" else (d.year >= 2023).astype(int)
        for v in ["z_access", "z_income", "z_urban"]:
            d["t_" + v] = d.cyber * k * d[v]
        out[name] = {}
        for key, ctrl in SETS.items():
            terms = ["t_z_access"] + ["t_" + v for v in ctrl]
            m = pf.fepois(f"cases ~ {' + '.join(terms)} | sc + st + ct", data=d, vcov={"CRV1": "state"})
            out[name][key] = res(m, terms)
    return out


def main():
    c = pd.read_csv(CTRL)
    r = {"levels_1b": levels(c), **models(c)}
    with open(OUT, "w") as f:
        json.dump(r, f, indent=2)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
