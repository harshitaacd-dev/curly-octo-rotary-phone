#!/usr/bin/env python3
"""Build reports/index.csv: one row per archived report, with the reporting
period the document itself states (filenames/labels from the platforms are
not always reliable).

Requires: pdftotext (poppler-utils), python-dateutil.
"""
import csv
import re
import subprocess
from pathlib import Path

from datetime import date

from dateutil import parser as dparser
from dateutil.relativedelta import relativedelta

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"

# Where each platform's reports were collected from. Meta and WhatsApp serve
# signed CDN links that expire, so the stable index page is recorded instead.
INDEX_PAGES = {
    "meta": "https://transparency.meta.com/reports/regulatory-transparency-reports/",
    "whatsapp": "https://www.whatsapp.com/legal/india-monthly-reports",
    "x": "https://transparency.x.com/en/reports/countries/in",
    "google": "https://transparencyreport.google.com/",
    "snap": "https://values.snap.com/privacy/transparency/india-transparency-page",
    "sharechat": "https://help.sharechat.com/transparency-report/",
    "moj": "https://help.mojapp.in/transparency-report/",
    "pinterest": "https://policy.pinterest.com/en/india-transparency-report",
    "roblox": "https://about.roblox.com/transparency",
}
PLATFORM_NAMES = {
    "meta": "Meta (Facebook, Instagram, Threads)",
    "whatsapp": "WhatsApp",
    "x": "X (Twitter)",
    "google": "Google (incl. YouTube)",
    "snap": "Snapchat",
    "sharechat": "ShareChat",
    "moj": "Moj",
    "pinterest": "Pinterest",
    "roblox": "Roblox",
}

DATE = r"(\d{4}-\d{2}-\d{2}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+,?\s+\d{4}|[A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})"
PERIOD_RES = [
    re.compile(r"period\s+(?:from\s+)?" + DATE + r"\s*(?:to|through to|through|-|–)\s*" + DATE, re.I),
    re.compile(r"(?:from|between)\s+" + DATE + r"\s*(?:to|through to|through|and|-|–)\s*" + DATE, re.I),
]
# The very first Meta/WhatsApp reports use "15 May-15 June, 2021".
SHORT_RE = re.compile(r"period\s+(?:from\s+)?(\d{1,2}\s+[A-Z][a-z]+)\s*[-–]\s*(\d{1,2}\s+[A-Z][a-z]+),?\s+(\d{4})", re.I)
PUBLISHED_RE = re.compile(r"Published on\s+" + DATE, re.I)


def pdf_text(path, pages=3):
    out = subprocess.run(["pdftotext", "-l", str(pages), str(path), "-"],
                         capture_output=True, text=True).stdout
    # Strip invisible formatting characters some PDFs embed (e.g. U+202D).
    out = re.sub(r"[​-‏‪-‮]", "", out)
    return re.sub(r"\s+", " ", out)


def iso(s):
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", s)
    return dparser.parse(s, dayfirst=False).date().isoformat()


def find_period(text):
    for rx in PERIOD_RES:
        m = rx.search(text)
        if m:
            try:
                return iso(m.group(1)), iso(m.group(2))
            except (ValueError, OverflowError):
                continue
    m = SHORT_RE.search(text)
    if m:
        return iso(f"{m.group(1)} {m.group(3)}"), iso(f"{m.group(2)} {m.group(3)}")
    return "", ""


def month_from_name(name):
    m = re.search(r"_(\d{4})-(\d{2})$", name)
    if not m:
        return "", ""
    y, mo = int(m.group(1)), int(m.group(2))
    import calendar
    return f"{y}-{mo:02d}-01", f"{y}-{mo:02d}-{calendar.monthrange(y, mo)[1]:02d}"


def main():
    rows = []
    for d in sorted(p for p in REPORTS.iterdir() if p.is_dir()):
        platform = d.name
        for f in sorted(d.glob("*.pdf")):
            txt_capture = f.with_suffix(".txt")
            row = {
                "platform": PLATFORM_NAMES.get(platform, platform),
                "file": str(f.relative_to(ROOT)),
                "period_start": "",
                "period_end": "",
                "published": "",
                "format": "web page snapshot" if txt_capture.exists() else "original PDF",
                "source": INDEX_PAGES.get(platform, ""),
                "notes": "",
            }
            if txt_capture.exists():
                # Web-page captures: the month is in the page title / filename.
                first = txt_capture.read_text().splitlines()[0]
                row["source"] = first.removeprefix("Source: ").strip()
                m = re.search(r"(\d{4}-\d{2})_to_(\d{4}-\d{2})", f.stem)
                if m:
                    row["period_start"] = m.group(1) + "-01"
                    row["period_end"] = month_from_name("_" + m.group(2))[1]
                    row["notes"] = "multi-month / annual report"
                else:
                    row["period_start"], row["period_end"] = month_from_name(f.stem)
            else:
                text = pdf_text(f)
                row["period_start"], row["period_end"] = find_period(text)
                pm = PUBLISHED_RE.search(text)
                if pm:
                    row["published"] = iso(pm.group(1))
                m = re.search(r"published_(\d{4}-\d{2}-\d{2})", f.stem)
                if m:
                    row["published"] = m.group(1)
                if platform == "x":
                    row["source"] = ("https://transparency.x.com/content/dam/"
                                     "transparency-twitter/country-reports/india/" + f.name)
                    # X names each file after its publication month M; it covers
                    # the 26th of M-2 to the 25th of M-1. Several PDFs repeat a
                    # stale or mistyped period in their opening sentence, so the
                    # filename is the reliable signal here.
                    pub = dparser.parse(f.stem.removeprefix("India-ITR-").replace("-", " 1 ")).date()
                    start = date(pub.year, pub.month, 1) - relativedelta(months=2)
                    expected = (start.replace(day=26).isoformat(),
                                (start + relativedelta(months=1)).replace(day=25).isoformat())
                    stated = (row["period_start"], row["period_end"])
                    row["period_start"], row["period_end"] = expected
                    if stated != expected:
                        row["notes"] = (f"PDF's opening sentence states {stated[0]} to {stated[1]}; "
                                        "data sections and X's monthly cadence indicate the period shown")
                if platform == "google":
                    import calendar
                    y, mo = map(int, f.stem.rsplit("_", 1)[1].split("-"))
                    last = calendar.monthrange(y, mo)[1]
                    row["source"] = ("https://storage.googleapis.com/transparencyreport/report-downloads/"
                                     f"india-intermediary-guidelines_{y}-{mo}-1_{y}-{mo}-{last}_en_v1.pdf")
                if not row["period_start"]:
                    row["period_start"], row["period_end"] = month_from_name(f.stem)
                    if row["period_start"]:
                        row["notes"] = "period taken from filename (not stated in a parseable form in the PDF)"
                    else:
                        row["notes"] = "period not detected automatically; see PDF"
            rows.append(row)

    rows.sort(key=lambda r: (r["platform"], r["period_start"], r["file"]))
    with open(REPORTS / "index.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} reports indexed")


if __name__ == "__main__":
    main()
