"""Shared helpers for turning archived reports into tidy datasets."""
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
DATASETS = ROOT / "datasets"

# Long ("tidy") layout shared by every platform dataset: one row per number.
FIELDS = ["platform", "service", "period_start", "period_end", "section",
          "category", "metric", "value", "unit", "notes", "source_file"]

_INVISIBLE = re.compile(r"[​-‏‪-‮⁠﻿]")


def pdf_text(path, layout=True):
    args = ["pdftotext"] + (["-layout"] if layout else []) + [str(ROOT / path), "-"]
    out = subprocess.run(args, capture_output=True, text=True).stdout
    out = _INVISIBLE.sub("", out).replace("\xa0", " ")
    out = re.sub(r"(\d),\s(\d{3})\b", r"\1,\2", out)  # "33, 061" -> "33,061"
    out = re.sub(r"(\d)[’'](\d{3})\b", r"\1,\2", out)  # "46’966" -> "46,966"
    # Some PDFs set the first letter of a table cell apart (a drop cap), so
    # "Content showing…" comes out as " ontent showing…" followed by a line
    # holding just "C". Put the letter back.
    return _DROP_CAP.sub(lambda m: m.group(1) + m.group(3) + m.group(2), out)


_DROP_CAP = re.compile(r"(?m)^([ \t]*)([a-z][^\n]*)\n[ \t]*([A-Z])[ \t]*$")


def num(s):
    """'1,23,456' / '27,762' / '5.4' / '0.5%' -> int/float; None if not numeric."""
    s = s.strip().rstrip("%").replace(",", "").replace(" ", "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    return float(s) if "." in s else int(s)


def index_rows(platform_dir):
    """Rows from reports/index.csv for one platform folder, keyed by file path."""
    with open(REPORTS / "index.csv") as fh:
        return {r["file"]: r for r in csv.DictReader(fh)
                if r["file"].startswith(f"reports/{platform_dir}/")}


def write(name, rows):
    DATASETS.mkdir(exist_ok=True)
    rows.sort(key=lambda r: (r["period_start"], r["service"], r["section"],
                             r["category"], r["metric"]))
    with open(DATASETS / f"{name}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, restval="")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


# Values as printed in tables: 1,234 / 12.5% / 676.4K / 1.8 M / 10.7L / Nil / N/A.
VALUE_RE = re.compile(r"^(?:[<>]?\s?[\d,]+(?:\.\d+)?\s?(?:[KMBL]|Cr)?%?|Nil|N/?A|Not Available|-{1,2}|—)$", re.I)
_SCALE = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000, "L": 100_000, "CR": 10_000_000}


def value(s):
    """Parse a printed table value. Returns (number or None, is_approximate).
    K/M/B, L (lakh) and Cr (crore) abbreviations are expanded and flagged as
    approximate. Bounds such as "<1 K" can't be turned into a number."""
    s = s.strip()
    if s.lower() == "nil":
        return 0, False
    if s[:1] in "<>":
        return None, True
    m = re.fullmatch(r"([\d,]+(?:\.\d+)?)\s?([KMBL]|Cr)", s, re.I)
    if m:
        return round(float(m.group(1).replace(",", "")) * _SCALE[m.group(2).upper()]), True
    return num(s), False


def parse_table(lines, row_start=None):
    """Turn a block of `pdftotext -layout` lines into [(label, [cells])].

    Cells are taken from the right-hand end of each line (columns are separated
    by 2+ spaces). Category labels that wrap onto extra lines are joined back
    together: a line with text but no values either opens a row (its values
    follow on a later line) or, if `row_start` doesn't match it / it starts in
    lower case, continues the previous label.
    """
    rows, open_row = [], None
    for raw in lines:
        if not raw.strip():
            continue
        parts = [p for p in re.split(r"\s{2,}", raw.strip()) if p]
        cells = []
        while parts and VALUE_RE.match(parts[-1]):
            cells.insert(0, parts.pop())
        label = " ".join(parts).strip()
        is_cont = bool(label) and (label[0].islower() or
                                   (row_start is not None and not row_start.match(label)))
        if label and not is_cont:
            open_row = [label, cells]
            rows.append(open_row)
            if cells:
                open_row = None
        elif label:  # continuation of a wrapped label
            target = open_row or (rows[-1] if rows else None)
            if target is None:
                continue
            target[0] += " " + label
            if cells and not target[1]:
                target[1] = cells
                open_row = None
        elif cells and open_row is not None:
            open_row[1] = cells
            open_row = None
    return [(lbl, c) for lbl, c in rows if c]
