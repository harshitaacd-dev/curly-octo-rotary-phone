"""Roblox India IT Rules reports -> datasets/roblox.csv

Table 1: grievance reports received via the India Grievance Officer channel
and enforcement actions taken, by category ("-" cells are left out: they are
not stated as zero). Table 2: proactive content moderation actions, which
Roblox says are GLOBAL, not India-only. Categories were revised in 2026.
"""
import re

from common import index_rows, parse_table, pdf_text, value, write


def main():
    rows = []
    for path, meta in index_rows("roblox").items():
        t = pdf_text(path)
        base = dict(platform="Roblox", period_start=meta["period_start"],
                    period_end=meta["period_end"], unit="count", source_file=path)
        i = t.rfind("Table 1: Grievance")  # skip the table of contents
        j = t.find("Table 2", i)
        for label, cells in parse_table(t[i:j].splitlines()[1:]):
            if len(cells) < 2 or "India IT Rules" in label or "Transparency Report" in label:
                continue
            cat = "All" if label.lower() in ("total", "grand total") else label
            for metric, cell in (("reports received", cells[-2]), ("enforcement actions", cells[-1])):
                v, _ = value(cell)
                if v is not None:
                    rows.append({**base, "service": "Roblox", "section": "user grievances",
                                 "category": cat, "metric": metric, "value": v})
        m = re.search(r"Proactive content moderation actions taken\s+([\d,]+)", t)
        if m:
            rows.append({**base, "service": "Roblox (global)",
                         "section": "proactive moderation (global, not India-only)",
                         "category": "All", "metric": "content moderation actions",
                         "value": value(m.group(1))[0]})
    write("roblox", rows)


if __name__ == "__main__":
    main()
