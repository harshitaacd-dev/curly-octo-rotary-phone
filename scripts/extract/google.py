"""Google (YouTube and other SSMI products) monthly reports -> datasets/google.csv

Each report has: total complaints, complaints by reason, total removal actions
on complaints, removal actions by reason, and removal actions from automated
detection. Older reports list reasons as "Copyright: 26,707 (96.2%)"; newer
ones use a two-column table.
"""
import re

from common import index_rows, num, pdf_text, write

REASON_RE = re.compile(r"^\s*([A-Z][A-Za-z ]+?)(?::\s*|\s{2,})([\d,]+)(?:\s*\([\d.]+%\))?\s*$")
SKIP = {"Category", "Reason", "Count"}


def section(text, start, end):
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start)) if end else -1
    return text[i:j if j > 0 else len(text)]


def headline_number(block):
    """The big stand-alone figure printed beside a section's description."""
    m = re.search(r"^\s*([\d,]{2,})\s*$", block, re.M)
    return num(m.group(1)) if m else None


def reasons(block):
    out = []
    for line in block.splitlines():
        m = REASON_RE.match(line)
        if m and m.group(1).strip() not in SKIP:
            out.append((m.group(1).strip(), num(m.group(2))))
    return out


def main():
    rows = []
    for path, meta in index_rows("google").items():
        t = pdf_text(path)
        base = dict(platform="Google", service="Google SSMI products (incl. YouTube)",
                    period_start=meta["period_start"], period_end=meta["period_end"],
                    unit="count", source_file=path)

        def add(section_, category, metric, value):
            if value is not None:
                rows.append({**base, "section": section_, "category": category,
                             "metric": metric, "value": value})

        # Sections end at the next heading; reasons stop before the FAQ pages.
        t = t.split("Frequently asked questions")[0].split("FAQs")[0]
        add("user complaints", "All", "complaints received",
            headline_number(section(t, "Number of complaints received", "Complaint reasons")))
        for cat, v in reasons(section(t, "Complaint reasons", "Removal actions")):
            add("user complaints", cat, "complaints received", v)

        add("user complaints", "All", "removal actions",
            headline_number(section(t, "Removal actions taken on complaints", "Reasons we take removal action")))
        for cat, v in reasons(section(t, "Reasons we take removal action", "Automated detection")):
            add("user complaints", cat, "removal actions", v)

        # Not reported in the first (April 2021) edition.
        add("automated detection", "All", "removal actions",
            headline_number(section(t, "Automated detection", None)))
    write("google", rows)


if __name__ == "__main__":
    main()
