"""WhatsApp monthly reports -> datasets/whatsapp.csv

Each report has: grievances by topic (received / accounts actioned), orders
from the Grievance Appellate Committee (from 2023), and accounts banned in
India, with the subset banned proactively (stated in the text from 2022).
"""
import re

from common import index_rows, num, pdf_text, write

CELL = r"([\d,]+|Nil|N/A|NA|-)"
TOPIC_RE = re.compile(r"^\s*([A-Z][A-Za-z ]+?)\s{2,}" + CELL + r"\s+" + CELL + r"\s*$")
# Total row whose label was pushed onto the next line ("8,841  6" / "Total").
ORPHAN_TOTAL_RE = re.compile(r"^\s*" + CELL + r"\s+" + CELL + r"\s*\n\s*Total\s*$", re.M | re.I)
# Fallback for PDFs whose -layout text is scrambled: one cell per line.
TOPICS = r"(Account support|Ban appeal|Other support|Product support|Safety issues|Safety|Total)"
PLAIN_ROW_RE = re.compile(TOPICS + r"\s*\n\s*" + CELL + r"\s*\n\s*" + CELL + r"\s*\n", re.I)


def cell(v):
    """'Nil' is a reported zero; 'N/A' means the measure does not apply."""
    if v == "Nil":
        return 0
    return num(v)


def main():
    rows = []
    for path, meta in index_rows("whatsapp").items():
        t = pdf_text(path)
        base = dict(platform="WhatsApp", service="WhatsApp",
                    period_start=meta["period_start"], period_end=meta["period_end"],
                    unit="count", source_file=path)

        def add(section, category, metric, value):
            if value is not None:
                rows.append({**base, "section": section, "category": category,
                             "metric": metric, "value": value})

        i = t.find("Table 1")
        j = t.find("Note", i)
        table = [(m.group(1).strip(), m.group(2), m.group(3))
                 for m in map(TOPIC_RE.match, t[i:j].splitlines())
                 if m and m.group(1).strip() != "Topic"]
        if table and not any(r[0].lower() == "total" for r in table):
            o = ORPHAN_TOTAL_RE.search(t[i:j])
            if o:
                table.append(("Total", o.group(1), o.group(2)))
        if not table:
            plain = pdf_text(path, layout=False)
            k = plain.find("Grievances from users in India")
            table = [(m.group(1), m.group(2), m.group(3))
                     for m in PLAIN_ROW_RE.finditer(plain[k:plain.find("Orders from the GAC", k)])]
        for topic, received, actioned in table:
            topic = "All" if topic.lower() == "total" else topic
            add("user grievances", topic, "reports received", cell(received))
            add("user grievances", topic, "accounts actioned", cell(actioned))

        g = re.search(r"Orders Received from the Grievance Appellate Committee.*?\n(?:.*\n)*?\s*"
                      + CELL + r"\s+" + CELL + r"\s*\n", t)
        if g:
            add("GAC orders", "All", "orders received", cell(g.group(1)))
            add("GAC orders", "All", "orders complied with", cell(g.group(2)))

        b = re.search(r"Indian accounts banned on WhatsApp[^\n]*\n(?:[^\n]*\n){0,8}?\s*([\d,]{5,})\s*\n", t)
        if b:
            add("accounts banned", "All", "accounts banned", num(b.group(1)))
        p = re.search(r"(\d[\d,]*)\s*of\s+these accounts were\s+proactively banned", t)
        if p:
            add("accounts banned", "All", "accounts banned proactively (before any user report)", num(p.group(1)))
    write("whatsapp", rows)


if __name__ == "__main__":
    main()
