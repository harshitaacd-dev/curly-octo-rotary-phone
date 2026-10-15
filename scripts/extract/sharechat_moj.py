"""ShareChat and Moj monthly pages (reports/<app>/*.txt) -> datasets/sharechat.csv, datasets/moj.csv

Both apps (same company, same template) report:
  1. law enforcement requests (received / user data provided / takedown taken)
  2. user reports/complaints: total, and by reason (count and/or % share;
     early months give only the % share)
  3. takedowns by type of content
  4. account bans by ban type and duration, plus accounts permanently terminated
Only monthly reports are used; the annual (2018-20) and the consolidated
Jun 2021 - Mar 2022 pages repeat or predate the monthly series.
"""
import re
from pathlib import Path

from common import ROOT, index_rows, num, write

SECTION_RE = re.compile(r"^(\d)\.\s+(.+)$")
MONTH_LINE = re.compile(r"^[A-Z][a-z]+ \d{4}$")
PAREN_RE = re.compile(r"^(.+?)\s*\(([\d.,]+%?)\)$")


def section_name(title):
    t = title.lower()
    if "law enforcement" in t:
        return "law enforcement requests"
    if "user" in t:
        return "user reports"
    if "takedown" in t:
        return "takedowns"
    if "ban" in t:
        return "account bans"
    return t


METRIC_NAMES = [  # wording that changed between months -> one name
    (r"^total number of user (complaints|reports) received", "user reports received"),
    (r"^content pieces taken down$", "content taken down"),
    (r"takedown.*(action|taken)", "requests where takedown/ban action was taken"),
]


def metric(name):
    name = name.lower().strip()
    for pat, new in METRIC_NAMES:
        if re.search(pat, name):
            return new
    return name


def val(s):
    """Table cell -> number. The apps print "None" for zero."""
    return 0 if s.strip() == "None" else num(s)


def is_value(s):
    return val(s) is not None


def run(app, platform):
    rows = []
    for path, meta in index_rows(app).items():
        if "_to_" in path:  # annual / consolidated pages
            continue
        lines = [l.rstrip() for l in Path(ROOT / path).with_suffix(".txt").read_text().splitlines()[3:]]
        base = dict(platform=platform, service=platform, period_start=meta["period_start"],
                    period_end=meta["period_end"], source_file=path)

        def add(section, category, metric_, val, unit="count"):
            if val is not None:
                rows.append({**base, "section": section, "category": category,
                             "metric": metric(metric_), "value": val, "unit": unit})

        section, header, prev_text = None, None, ""
        for line in lines:
            s = line.strip()
            if not s:
                continue
            m = SECTION_RE.match(s)
            if m:
                section, header = section_name(m.group(2)), None
                continue
            if section is None:
                continue
            if MONTH_LINE.match(s):
                header = None
                continue
            if "\t" in line:
                cells = [c.strip() for c in line.split("\t")]
                if all(not is_value(c) for c in cells[1:]) and len(cells) > 1 and not is_value(cells[0]):
                    header = cells
                    continue
                if is_value(cells[0]):  # unlabelled row of totals under a header
                    for h, c in zip(header or [], cells):
                        add(section, "All", h.lower(), val(c))
                    continue
                label, vals = cells[0], cells[1:]
                if header and len(header) == len(cells):
                    for h, c in zip(header[1:], vals):
                        if section == "account bans":
                            add(section, f"{h} ({label})", "accounts banned", val(c))
                        else:
                            pct = c.endswith("%")
                            add(section, label, "share of user reports" if pct else h.lower(),
                                val(c), "percent" if pct else "count")
                elif len(vals) == 1:  # "Total number of user reports received ...<tab>3,994,260"
                    add(section, "All", re.sub(r"\s+for (ShareChat|Moj)$", "", label).lower(), num(vals[0]))
                continue
            p = PAREN_RE.match(s)
            if p and section in ("user reports", "takedowns"):
                v = p.group(2)
                if v.endswith("%"):
                    add(section, p.group(1), "share of user reports", num(v), "percent")
                else:
                    add(section, p.group(1), "content taken down", num(v))
                continue
            if is_value(s) and prev_text.lower().startswith("total number"):
                add(section, "All", prev_text.lower(), num(s))
                continue
            if re.search(r"have not received law enforcement requests", s):
                add("law enforcement requests", "All", "law enforcement requests received", 0)
            t = re.search(r"permanently terminated ([\d,]+) user accounts", s)
            if t:
                add("account bans", "Permanent termination", "accounts terminated", num(t.group(1)))
            prev_text = s
    write(app, rows)


if __name__ == "__main__":
    run("sharechat", "ShareChat")
    run("moj", "Moj")
