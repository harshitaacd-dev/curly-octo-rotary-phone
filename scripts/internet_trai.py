"""India internet subscribers from TRAI's quarterly Performance Indicator Reports (PIR).

Usage: python scripts/internet_trai.py data/external/trai data/clean

Reads the December-quarter report for each year (qpir_dec_YYYY.pdf, 2004-2025) plus the
latest one (qpir_jun_2026.pdf) and writes:
  india_internet_trai.csv   one row per report date: total / broadband / narrowband / wired /
                            wireless / urban / rural internet subscribers (million) and
                            subscribers per 100 population
  state_internet_trai.csv   State/UT x report date, Dec 2021 onwards (TRAI's first State/UT
                            internet table): rural / urban / total subscribers (million) and
                            subscribers per 100 population. State names follow the NCRB files.

2004-2012 are typed in from each report's summary (their layouts differ); 2013 onwards are
parsed from the report's "Snapshot" page. Needs pdftotext (poppler-utils).

Series breaks (see data/external/trai/README.md):
  * Up to Dec 2012 TRAI counted only wired/dongle internet subscribers and reported phones
    able to use data separately ("wireless data subscribers"). From Dec 2013 the total includes
    internet access on mobile phones, so 2012 -> 2013 jumps from 25 to 239 million.
  * Broadband = download speed >= 256 kbps to 2012, >= 512 kbps 2013-2022, >= 2 Mbps from 2023.
  * Subscriptions, not people: one person with two SIMs counts twice.
"""
import csv, os, re, subprocess, sys

# Dec reports 2004-2012, figures as printed in that report (million). wireless_data = handsets
# able to access data services, reported separately and not part of the total.
EARLY = {
    2004: dict(total=5.45, broadband=0.047),                      # summary table; BB = 46,638
    2005: dict(total=6.70, broadband=0.903),
    2006: dict(total=8.582, broadband=2.054),                     # 85.82 lakh; BB 20.54 lakh
    2007: dict(total=10.36, broadband=3.13, wireless_data=57.83),
    2008: dict(total=12.85, broadband=5.52, wireless_data=101.10),
    2009: dict(total=15.24, broadband=7.82, narrowband=7.42, wireless_data=149.03),
    2010: dict(total=18.69, broadband=10.99, narrowband=7.70, wireless_data=332.43),
    2011: dict(total=22.39, broadband=13.35, narrowband=9.04, wireless_data=431.37),
    2012: dict(total=25.33, broadband=14.98, narrowband=10.35, wireless_data=430.60),
}
NUM = r"([\d,]+\.?\d*)"
SNAPSHOT = {  # label regex -> column; first match after "Total Internet Subscribers"
    "total": r"^\s*Total Internet Subscribers\s+" + NUM + r"\s*[Mm]illion",
    "narrowband": r"^\s*Narrowband [Ss]ubscribers\s+" + NUM,
    "broadband": r"^\s*Broadband [Ss]ubscribers\s+" + NUM,
    "wired": r"^\s*(?:Wired|Fixed \(Wired\) Access) Internet Subscribers\s+" + NUM,
    "wireless": r"^\s*Wireless (?:\(Fixed\+Mobile\) Access )?Internet Subscribers\s+" + NUM,
    "urban": r"^\s*Urban Internet Subscribers\s+" + NUM + r"\s*[Mm]illion",
    "rural": r"^\s*Rural Internet Subscribers\s+" + NUM + r"\s*[Mm]illion",
    "per100": r"^\s*Total Internet Subscribers per(?: 100 population)?\s+" + NUM,
    "urban_per100": r"^\s*Urban Internet Subscribers per(?: 100 population)?\s+" + NUM,
    "rural_per100": r"^\s*Rural Internet Subscribers per(?: 100 population)?\s+" + NUM,
}
NAT_COLS = ["total", "broadband", "narrowband", "wired", "wireless", "urban", "rural",
            "per100", "urban_per100", "rural_per100", "wireless_data"]
STATE_NAME = [  # (regex on TRAI's name, NCRB name); first match wins
    (r"Andaman|A ?& ?N\b", "A&N Islands"), (r"Dad[ar]+ & Nagar|Daman", "D&N Haveli and Daman & Diu"),
    (r"Andhra", "Andhra Pradesh"), (r"Arunachal", "Arunachal Pradesh"), (r"Assam", "Assam"),
    (r"Bihar", "Bihar"), (r"Chh?att?isgarh", "Chhattisgarh"), (r"Goa", "Goa"),
    (r"Gujarat", "Gujarat"), (r"Haryana", "Haryana"), (r"Himachal", "Himachal Pradesh"),
    (r"Jammu", "Jammu & Kashmir"), (r"Jharkhand", "Jharkhand"), (r"Karnataka", "Karnataka"),
    (r"Kerala", "Kerala"), (r"Madhya", "Madhya Pradesh"), (r"Maharashtra", "Maharashtra"),
    (r"Manipur", "Manipur"), (r"Meghalaya", "Meghalaya"), (r"Mizoram", "Mizoram"),
    (r"Nagaland", "Nagaland"), (r"Odisha|Orissa", "Odisha"), (r"Punjab", "Punjab"),
    (r"Rajasthan", "Rajasthan"), (r"Sikkim", "Sikkim"), (r"Tamil", "Tamil Nadu"),
    (r"Telangana", "Telangana"), (r"Tripura", "Tripura"), (r"Uttar Pradesh", "Uttar Pradesh"),
    (r"Uttarakhand", "Uttarakhand"), (r"West Bengal", "West Bengal"), (r"Chandigarh", "Chandigarh"),
    (r"Delhi", "Delhi"), (r"Ladakh", "Ladakh"), (r"dweep", "Lakshadweep"),
    (r"Pud[du]ch?er+y|Puduchery", "Puducherry"), (r"^\s*Total\s*$", "All India"),
]
UTS = {"A&N Islands", "D&N Haveli and Daman & Diu", "Chandigarh", "Delhi", "Jammu & Kashmir",
       "Ladakh", "Lakshadweep", "Puducherry"}
TOKEN = re.compile(r"^(-|\d[\d,]*\.?\d*)$")


def pdf_lines(path):
    out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True)
    return out.stdout.splitlines()


def num(s):
    return None if s in (None, "-") else float(s.replace(",", ""))


def snapshot(lines):
    start = next(i for i, l in enumerate(lines) if re.search(SNAPSHOT["total"], l))
    row = {}
    for l in lines[start:start + 40]:
        for col, rx in SNAPSHOT.items():
            m = re.search(rx, l)
            if m and col not in row:
                row[col] = num(m.group(1))
    return row


def state_table(lines):
    """Rows of 'State/UT wise number of Internet Subscribers per 100 population'."""
    start = next(i for i, l in enumerate(lines)
                 if re.search(r"State/UT wise number of Internet Subscribers per 100", l))
    rows, pending = [], []
    for l in lines[start + 1:start + 120]:
        parts = l.split()
        k = len(parts)
        while k and TOKEN.match(parts[k - 1]):
            k -= 1
        values, name = parts[k:], " ".join(parts[:k])
        if len(values) >= 6 and (name or pending):
            # A wrapped name (e.g. "Uttar Pradesh / 26 / (UPE+UPW)") has its pieces on the
            # lines above; the leading serial number may sit with the values.
            label = name if re.search(r"[A-Za-z]", name) else " ".join(pending)
            state = next((s for rx, s in STATE_NAME if re.search(rx, label, re.I)), None)
            if state is None:
                raise ValueError(f"unknown State/UT name: {label!r}")
            rows.append([state] + [num(v) for v in values[-6:]])
            pending = []
            if state == "All India":
                return rows
        elif re.search(r"[A-Za-z]", l) and not re.search(r"Subscribers|Rural|S\.N\.|Union Terr", l):
            pending.append(re.sub(r"^\s*\d+\s+", "", l.strip()))
        elif re.search(r"Union Terr", l):
            pending = []
    raise ValueError("State/UT table has no Total row")


def main(src, out_dir):
    reports = [(f"{y}-12-31", f"qpir_dec_{y}.pdf") for y in range(2004, 2026)]
    reports.append(("2026-06-30", "qpir_jun_2026.pdf"))
    nat, states = [], []
    for as_of, fname in reports:
        year = int(as_of[:4])
        lines = pdf_lines(os.path.join(src, fname))
        row = dict(EARLY[year]) if year in EARLY else snapshot(lines)
        bb = "256 kbps" if year <= 2012 else "512 kbps" if year <= 2022 else "2 Mbps"
        scope = "wired + dongle only (excludes mobile phones)" if year <= 2012 else "all (incl. mobile)"
        nat.append([as_of] + [row.get(c) for c in NAT_COLS] + [scope, bb, fname])
        if year >= 2021:
            for r in state_table(lines):
                rtype = "total_india" if r[0] == "All India" else "ut" if r[0] in UTS else "state"
                states.append([as_of, year, r[0], rtype] + r[1:] + [fname])
        print(f"{as_of}: total {row.get('total')} mn", file=sys.stderr)

    # Checks: wired + wireless = total, urban + rural = total, States add up to All India.
    for r in nat:
        d = dict(zip(["as_of"] + NAT_COLS, r))
        for a, b in (("wired", "wireless"), ("urban", "rural"), ("broadband", "narrowband")):
            if d[a] is not None and d[b] is not None and abs(d[a] + d[b] - d["total"]) > 0.1:
                print(f"warning {d['as_of']}: {a}+{b} = {d[a] + d[b]:.2f} != total {d['total']}",
                      file=sys.stderr)
    for as_of in sorted({s[0] for s in states}):
        rows = [s for s in states if s[0] == as_of]
        india = next(s for s in rows if s[3] == "total_india")
        tot = sum(s[6] for s in rows if s[3] != "total_india")
        if abs(tot - india[6]) > 0.5:
            print(f"warning {as_of}: States sum to {tot:.2f}, All India {india[6]}", file=sys.stderr)
        if len(rows) != 37:
            print(f"warning {as_of}: {len(rows)} rows, expected 36 States/UTs + All India", file=sys.stderr)

    with open(os.path.join(out_dir, "india_internet_trai.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["as_of", "internet_subs_mn", "broadband_subs_mn", "narrowband_subs_mn",
                    "wired_subs_mn", "wireless_subs_mn", "urban_subs_mn", "rural_subs_mn",
                    "subs_per100", "urban_subs_per100", "rural_subs_per100",
                    "wireless_data_capable_subs_mn", "coverage", "broadband_min_speed", "source_file"])
        w.writerows(nat)
    with open(os.path.join(out_dir, "state_internet_trai.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["as_of", "year", "state", "row_type", "rural_subs_mn", "urban_subs_mn",
                    "internet_subs_mn", "rural_subs_per100", "urban_subs_per100", "subs_per100",
                    "source_file"])
        w.writerows(states)


if __name__ == "__main__":
    main(*sys.argv[1:3])
