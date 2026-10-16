"""India internet access indicators from the World Bank API (ITU-sourced), 2004 onwards.

Usage: python scripts/internet_worldbank.py data/clean/india_internet_worldbank.csv

One row per year. `internet_users_mn` is derived: share of population using the internet x
total population. The World Bank republishes ITU's figures; ITU's India series is itself an
estimate (from 2020 it is modelled on NSS/household survey and TRAI subscriber data), so read
year-on-year jumps with care.
"""
import csv, json, sys, urllib.request

START = 2004
INDICATORS = {
    "internet_users_pct": "IT.NET.USER.ZS",          # Individuals using the Internet (% of population)
    "fixed_broadband_subs": "IT.NET.BBND",            # Fixed broadband subscriptions
    "fixed_broadband_per100": "IT.NET.BBND.P2",       # Fixed broadband subscriptions per 100 people
    "mobile_subs": "IT.CEL.SETS",                     # Mobile cellular subscriptions
    "mobile_per100": "IT.CEL.SETS.P2",                # Mobile cellular subscriptions per 100 people
    "fixed_telephone_per100": "IT.MLT.MAIN.P2",       # Fixed telephone subscriptions per 100 people
    "secure_servers_per_mn": "IT.NET.SECR.P6",        # Secure Internet servers per 1 million people
    "population": "SP.POP.TOTL",
}
URL = "https://api.worldbank.org/v2/country/IND/indicator/{}?format=json&date={}:2030&per_page=200"


def fetch(code):
    with urllib.request.urlopen(URL.format(code, START), timeout=60) as r:
        meta, rows = json.load(r)
    return {int(x["date"]): x["value"] for x in rows or []}, meta.get("lastupdated", "")


def main(out):
    data, updated = {}, ""
    for col, code in INDICATORS.items():
        data[col], updated = fetch(code)
    years = sorted({y for d in data.values() for y, v in d.items() if v is not None})
    cols = ["year"] + list(INDICATORS) + ["internet_users_mn", "source_lastupdated"]
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for y in years:
            row = {c: data[c].get(y) for c in INDICATORS}
            pct, pop = row["internet_users_pct"], row["population"]
            users = round(pct / 100 * pop / 1e6, 2) if pct is not None and pop else None
            vals = [y] + [round(v, 4) if isinstance(v, float) else v for v in row.values()]
            w.writerow(vals + [users, updated])
    print(f"wrote {out}: {years[0]}-{years[-1]}")


if __name__ == "__main__":
    main(sys.argv[1])
