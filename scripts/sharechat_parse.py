"""Parse ShareChat and Moj monthly IT Rules transparency reports into one CSV.

Usage: python scripts/sharechat_parse.py
Input:  data/external/platform_reports/sharechat_raw/<app>_<year>_<month>.html, saved from
        https://help.sharechat.com/transparency-report/<month>-<year>/ and
        https://help.mojapp.in/transparency-report/<month>-<year>/  (June 2021 - October 2022)
Output: data/external/platform_reports/sharechat.csv, one row per app x month x reason:
        app, month, reason, count, share_pct, total_reports, derived_from_share

Both apps belong to Mohalla Tech. Their public report pages stop at October 2022: later month
URLs redirect to the help home page. Two formats: up to April 2022 the report gives the total
and each reason's percentage (count = total x share, derived_from_share = 1); from May 2022 it
gives each reason's count and percentage.
"""
import glob, os, re

import pandas as pd

RAW = "data/external/platform_reports/sharechat_raw"
OUT = "data/external/platform_reports/sharechat.csv"
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def text(path):
    t = open(path, encoding="utf-8").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def num(s):
    return int(s.replace(",", ""))


def parse(path):
    app, year, month = os.path.basename(path)[:-5].split("_")
    x = text(path)
    rows = []
    m_new = re.search(r"received a total of ([\d,]+) user reports", x)
    if m_new:
        total = num(m_new.group(1))
        seg = x[x.find("Contribution percentage"):]
        seg = seg[:re.search(r"\d\. (Removal|Enforcement)", seg).start()]
        for reason, cnt, pct in re.findall(r"([A-Za-z][A-Za-z/'&\- ]*?) ([\d,]+) ([\d.]+)%", seg):
            rows.append((reason.strip(), num(cnt), float(pct), 0))
    else:
        total = num(re.search(r"Total number of user complaints received ([\d,]+)", x).group(1))
        seg = x[x.find("Categories of user complaints"):]
        seg = seg[:re.search(r"\d\. (Removal|Enforcement)", seg).start()]
        for reason, pct in re.findall(r"([A-Za-z][A-Za-z/'&\- ]*?) \(([\d.]+)%\)", seg):
            rows.append((reason.strip(), round(total * float(pct) / 100), float(pct), 1))
    reason_fix = {"Contribution percentage of user complaints received": None}
    out = []
    for reason, cnt, pct, derived in rows:
        reason = re.sub(r"^(Contribution percentage of user complaints received|Categories of user complaints received|Reasons Content and accounts reported) ", "", reason)
        if reason in reason_fix:
            continue
        out.append({"app": "ShareChat" if app == "sharechat" else "Moj",
                    "month": f"{year}-{MONTHS[month]:02d}", "reason": reason, "count": cnt, "share_pct": pct,
                    "total_reports": total, "derived_from_share": derived})
    return out


def main():
    rows = [r for f in sorted(glob.glob(os.path.join(RAW, "*.html"))) for r in parse(f)]
    d = pd.DataFrame(rows).sort_values(["app", "month", "count"], ascending=[True, True, False])
    d.to_csv(OUT, index=False)
    chk = d.groupby(["app", "month"]).agg(n=("reason", "size"), pct=("share_pct", "sum"), total=("total_reports", "first"))
    print(chk.to_string())
    print(sorted(d.reason.unique()))


if __name__ == "__main__":
    main()
