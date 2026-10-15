"""Monthly platform x category grievance panel from the IT Rules compliance reports.

Usage: python scripts/platform_panel.py data/external/india_it_rules_reports.xlsx data/clean/platform_grievances_monthly.csv

Keeps the user-initiated grievance series of X, Facebook, Instagram and Google (India only) and
maps each category to a group:
  synthetic      X "Misinformation / Synthetic and Manipulated Media" (X only)
  sexual         X sensitive adult content; Meta "content showing me in nudity ... sexual act";
                 Google graphic sexual content
  impersonation  X impersonation; Meta "fake profile pretending to be me"; Google impersonation
  harassment     X abuse/harassment; Meta bullying or harassment
  child          X child sexual exploitation
  placebo        everything else (copyright, hacked accounts, data requests, hateful conduct, ...)
From Sep 2025 X publishes a total and category shares; counts are rebuilt as total x share and
flagged (`derived_from_share`), and category names change, so the X analysis stops at Feb 2025
by default (see scripts/partA_estimate.py).
"""
import sys
import pandas as pd

SERIES = [  # platform, service, section, metric
    ("X", "X", "user grievances", "grievances received"),
    ("Meta", "Facebook", "user grievances", "reports received"),
    ("Meta", "Instagram", "user grievances", "reports received"),
    ("Google", "Google SSMI products (incl. YouTube)", "user complaints", "complaints received"),
]
GROUP = {
    "Misinformation / Synthetic and Manipulated Media": "synthetic",
    "Synthetic and manipulated media as defined in X’s authenticity policy": "synthetic",
    "Sensitive Adult Content": "sexual", "Sensitive adult content": "sexual",
    "Content showing me in nudity/partial nudity or in a sexual act": "sexual",
    "Graphic Sexual Content": "sexual",
    "Impersonation": "impersonation", "Fake profile that's pretending to be me": "impersonation",
    "Abuse / Harassment": "harassment", "Harassment": "harassment", "Bullying or Harassment": "harassment",
    "Child Sexual Exploitation": "child", "Child sexual exploitation": "child",
}
# X category names after the Sep 2025 format change -> earlier names
X_RENAME = {
    "Synthetic and manipulated media as defined in X’s authenticity policy": "Misinformation / Synthetic and Manipulated Media",
    "Sensitive adult content": "Sensitive Adult Content", "Harassment": "Abuse / Harassment",
    "Child sexual exploitation": "Child Sexual Exploitation", "Private information": "Privacy Infringement",
    "Promoting suicide or self-harm": "Promoting Suicide or Self-Harm", "Ban evasion": "Ban Evasion",
    "Intellectual property": "IP-related Infringement", "Other illegal content": "Illegal Activities",
}


def main(src, out):
    d = pd.read_excel(src, sheet_name="All data")
    parts = []
    for p, svc, sec, met in SERIES:
        s = d[(d.platform == p) & (d.service == svc) & (d.section == sec) & (d.metric == met) & (d.category != "All")]
        s = s.groupby(["month", "category"], as_index=False)["value"].sum()
        s["platform"] = svc if p == "Meta" else p
        s["derived_from_share"] = False
        parts.append(s)
    # X from Sep 2025: total x share
    x = d[(d.platform == "X") & (d.section == "user grievances")]
    tot = x[(x.metric == "reports received") & (x.category == "All")].set_index("month")["value"]
    sh = x[x.metric == "share of reports received"].copy()
    sh["value"] = (sh["month"].map(tot) * sh["value"] / 100).round()
    sh = sh[["month", "category", "value"]].assign(platform="X", derived_from_share=True)
    parts.append(sh)
    panel = pd.concat(parts, ignore_index=True)
    panel.loc[panel.platform == "X", "category"] = panel.loc[panel.platform == "X", "category"].replace(X_RENAME)
    panel = panel[~((panel.platform == "X") & (panel.category == "Other"))]  # appears in one month only
    panel["group"] = panel["category"].map(GROUP).fillna("placebo")
    panel = panel.rename(columns={"value": "count"})[["platform", "category", "group", "month", "count", "derived_from_share"]]
    panel = panel.sort_values(["platform", "category", "month"])
    panel.to_csv(out, index=False)
    print(panel.groupby(["platform", "group"])["month"].agg(["min", "max", "nunique"]).to_string(), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
