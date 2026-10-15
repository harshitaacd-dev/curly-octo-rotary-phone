"""Meta (Facebook, Instagram, Threads) monthly reports -> datasets/meta.csv

Each report has, per service:
  * content actioned and proactive rate by policy area (Tables "Content
    Actioned and Proactive Rate on <service>"). Counts are printed rounded
    (e.g. 676.4K, 1.8 M, 10.7L) so they are stored as approximate values;
  * grievances from users in India: reports received by category, reports
    where tools were provided, and (in the text) reports needing specialised
    review and reports actioned;
  * orders from the Grievance Appellate Committee (from 2023).
"""
import re

from common import index_rows, parse_table, pdf_text, value, write

SERVICES = ("Facebook", "Instagram", "Threads")
TABLE_RE = re.compile(r"^\s*Table \d+:\s*(.*)$")
BLOCK_END = re.compile(r"^\s*(Table \d+|Of\s*(these|the)|To understand|Note|Between|\*|This part|"
                       r"Facebook\s*$|Instagram\s*$|Threads\s*$)")
SERVICE_HEADING = re.compile(r"^\s*(Facebook|Instagram|Threads)\s*$")
# "1. Hate Speech"; some PDFs print the number on another line (". Hate Speech").
POLICY_ROW = re.compile(r"^(\d+)?\s*\.\s")


def clean_label(s):
    s = re.sub(r"^\d*\s*\.\s*", "", s)
    s = re.sub(r"\s\d{1,2}(?=\s|$)", " ", s)  # row numbers displaced into the label
    s = s.replace("*", "")
    return re.sub(r"\s+", " ", s).strip()


# Same category spelled differently across reports / services.
CANONICAL = {
    "content i appear in that i do not want displayed": "Content I appear in that I do not want displayed",
    "lost access to a page or group i used to manage": "Lost access to a page or group I used to manage",
}


def canonical(cat):
    key = re.sub(r"[^a-z ]", "", cat.lower())
    key = re.sub(r"\s+", " ", key).strip()
    return CANONICAL.get(key, cat)


def grievance_metric(title):
    t = title.lower().strip()
    if t.startswith("reports received"):
        return "reports received"
    if "tools" in t:
        return "reports where tools were provided"
    if "specialized review" in t or "specialised review" in t:
        return "reports needing specialised review"
    if "action" in t:
        return "reports actioned"
    return t


def main():
    rows = []
    for path, meta in index_rows("meta").items():
        t = pdf_text(path)
        lines = t.splitlines()
        base = dict(platform="Meta", period_start=meta["period_start"],
                    period_end=meta["period_end"], source_file=path)

        def add(service, section, category, metric, val, unit):
            if val is not None:
                rows.append({**base, "service": service, "section": section,
                             "category": category, "metric": metric, "value": val, "unit": unit})

        service = None
        for n, line in enumerate(lines):
            h = SERVICE_HEADING.match(line)
            if h:
                service = h.group(1)
                continue
            m = TABLE_RE.match(line)
            if not m:
                continue
            title = m.group(1)
            block = []
            for nxt in lines[n + 1:]:
                if BLOCK_END.match(nxt):
                    break
                block.append(nxt)

            if "Content Actioned and Proactive Rate" in title:
                svc = next((s for s in SERVICES if s in title), service)
                for label, cells in parse_table(block, row_start=POLICY_ROW):
                    cat = clean_label(label)
                    count, approx = value(cells[0])
                    add(svc, "proactive enforcement", cat, "content actioned", count,
                        "count (rounded in source)" if approx else "count")
                    if len(cells) >= 2:
                        rate, _ = value(cells[-1].replace("%", ""))
                        add(svc, "proactive enforcement", cat, "proactive rate", rate, "percent")
            elif "Grievance Appellate Committee" in title:
                g = re.search(r"^\s*([\d,]+|Nil)\s+([\d,]+|Nil|N/A)\s*$", "\n".join(block), re.M)
                if g:
                    add("All", "GAC orders", "All", "orders received", value(g.group(1))[0], "count")
                    add("All", "GAC orders", "All", "orders complied with", value(g.group(2))[0], "count")
            elif service:
                metric = grievance_metric(title)
                for label, cells in parse_table(block):
                    cat = clean_label(label)
                    if cat.lower() in ("category", "total number of reports"):
                        continue
                    cat = "All" if cat.lower() == "total" else canonical(cat)
                    add(service, "user grievances", cat, metric, value(cells[-1])[0], "count")

        # Totals stated in the running text of each service's grievance section.
        parts = re.split(r"^\s*(Facebook|Instagram|Threads)\s*$", t, flags=re.M)
        for svc, body in zip(parts[1::2], parts[2::2]):
            body = re.sub(r"\s+", "", body)  # some PDFs lose the spaces between words
            s = re.search(r"Oftheother([\d,]+)reportswherespecializedreviewwasneeded", body)
            if s:
                add(svc, "user grievances", "All", "reports needing specialised review", value(s.group(1))[0], "count")
            a = re.search(r"wetookactionon([\d,]+)reports?intotal", body)
            if a:
                add(svc, "user grievances", "All", "reports actioned", value(a.group(1))[0], "count")
    write("meta", rows)


if __name__ == "__main__":
    main()
