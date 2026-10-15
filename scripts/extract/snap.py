"""Snapchat India pages (saved as reports/snap/*.txt) -> datasets/snap.csv

The pages are tables whose cells come out one per line:
    <section title>
    <metric name> ... (k lines)
    <k totals>
    Reason
    <k column names>
    <category> <k numbers>   (repeated)
and, at the end, a "CSAM/CSEA: Total Account Deletions/Disabled" style block.
Sections: "Account / Content Violations" (to Nov 2024); from Dec 2024 the page
splits into an overview, reports to safety teams, and proactive detection.
"""
import re
from pathlib import Path

from common import ROOT, index_rows, num, write

FOOTER = {"COMPANY", "Back to India Transparency Reports"}
SKIP_HEAD = {"NEWS", "INVESTORS", "CAREERS", "Snap Values", "Policy", "Privacy", "Safety",
             "Transparency", "News", "Transparency Reports", "Resources"}


EMPTY = "<empty cell>"
SECTIONS = [  # (start of heading, lower case) -> section name used in the dataset
    ("account / content violations", "reports and enforcement"),
    ("overview of our trust & safety", "all enforcement (overview)"),
    ("community guidelines violations reported", "reported to safety teams"),
    ("proactive detection and enforcement", "proactive detection"),
]


def section_name(title):
    for start, name in SECTIONS:
        if title.lower().startswith(start):
            return name
    return None
# "1.644" printed where every other month has a whole count: a thousands separator.
DOTTED_THOUSANDS = re.compile(r"^\d{1,3}\.\d{3}$")


BOUND = re.compile(r"^[<>]\s?\d+(\.\d+)?$")  # e.g. "<1" minute


def is_num(s):
    return s == EMPTY or bool(BOUND.match(s)) or num(s) is not None


def split_cells(lines):
    """Pages saved with tab-separated rows -> one cell per line, keeping empty
    cells as placeholders so values stay under the right column."""
    for ln in lines:
        if "\t" in ln:
            for cell in ln.split("\t"):
                yield cell.strip() or EMPTY
        else:
            yield ln


def groups(lines):
    """Yield (text_lines, number_lines) runs."""
    text, nums = [], []
    for ln in lines:
        if is_num(ln):
            nums.append(ln)
        else:
            if nums:
                yield text, nums
                text, nums = [], []
            text.append(ln)
    if nums:
        yield text, nums


def metric_name(s):
    s = re.sub(r"^Total\s+", "", s).replace("*", "").strip()
    return s.lower()


def parse_value(s, unit):
    if s == EMPTY or BOUND.match(s):  # bounds such as "<1" have no single value
        return None, ""
    if unit == "count" and DOTTED_THOUSANDS.match(s):
        return int(s.replace(".", "")), f"printed as {s}; read as a thousands separator"
    return num(s), ""


def main():
    rows = []
    for path, meta in index_rows("snap").items():
        txt = Path(ROOT / path).with_suffix(".txt").read_text().splitlines()[3:]
        lines = []
        for ln in split_cells(x.strip() for x in txt):
            if ln in FOOTER:
                break
            if ln and ln not in SKIP_HEAD and not re.match(r"^India: \w+ \d{4}$", ln):
                lines.append(ln)
        base = dict(platform="Snapchat", service="Snapchat", period_start=meta["period_start"],
                    period_end=meta["period_end"], unit="count", source_file=path)
        section, headers = None, []
        for text, nums in groups(lines):
            k = len(nums)
            reason = [n for n, t in enumerate(text) if t in ("Reason", "Policy Reason")]
            if reason:
                i = reason[0]
                headers = text[i + 1:i + 1 + k]
                cats = text[i + 1 + k:]
                if text[:i]:
                    section = section_name(text[i - 1]) or section
            elif any(t.startswith("Total") or ":" in t for t in text):
                # A totals block: [section title...] + k metric names + k numbers.
                names, titles = text[-k:], text[:-k]
                if titles:
                    section = section_name(titles[-1]) or section
                for name, raw in zip(names, nums):
                    v, note = parse_value(raw, "count")
                    if v is None:
                        continue
                    if ":" in name:  # "CSAM: Total Account Deletions"
                        cat, met = (p.strip() for p in name.split(":", 1))
                        rows.append({**base, "section": "account deletions", "category": cat,
                                     "metric": metric_name(met), "value": v, "notes": note})
                    else:
                        rows.append({**base, "section": section, "category": "All",
                                     "metric": metric_name(name), "value": v, "notes": note})
                headers = []
                continue
            else:
                cats = text
            if not headers or not cats or len(headers) != k:
                continue
            cat = cats[-1]  # earlier names in the run had empty rows
            for h, raw in zip(headers, nums):
                unit = "minutes (median)" if "Turnaround" in h else "count"
                v, note = parse_value(raw, unit)
                if v is None:
                    continue
                rows.append({**base, "section": section, "category": cat,
                             "metric": metric_name(h), "value": v, "unit": unit, "notes": note})
    write("snap", rows)


if __name__ == "__main__":
    main()
