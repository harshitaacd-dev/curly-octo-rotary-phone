"""Cross-check every dataset: wherever a table gives a total ("All") and a
breakdown by category, compare the two. Writes datasets/validation.csv.

A difference does not by itself mean an extraction error: the platforms'
own tables often do not add up (missing categories, typos, double counting).
Each difference listed here was checked against the source document when the
datasets were built; see datasets/README.md.
"""
import csv
from collections import defaultdict

from common import DATASETS

PLATFORM_FILES = ["google", "meta", "whatsapp", "x", "snap", "sharechat", "moj", "pinterest", "roblox"]


def main():
    out = []
    for name in PLATFORM_FILES:
        groups = defaultdict(lambda: {"total": None, "sum": 0, "n": 0})
        with open(DATASETS / f"{name}.csv") as fh:
            for r in csv.DictReader(fh):
                # Unique-account counts overlap across categories by design.
                if r["unit"] != "count" or "unique" in r["metric"]:
                    continue
                key = (r["platform"], r["period_start"], r["period_end"], r["service"],
                       r["section"], r["metric"], r["source_file"])
                g = groups[key]
                if r["category"] == "All":
                    g["total"] = int(float(r["value"]))
                else:
                    g["sum"] += int(float(r["value"]))
                    g["n"] += 1
        for key, g in groups.items():
            if g["total"] is None or g["n"] == 0:
                continue
            platform, start, end, service, section, metric, src = key
            out.append(dict(platform=platform, period_start=start, period_end=end, service=service,
                            section=section, metric=metric, stated_total=g["total"],
                            sum_of_categories=g["sum"], difference=g["sum"] - g["total"],
                            categories=g["n"], source_file=src))
    out.sort(key=lambda r: (r["platform"], r["period_start"], r["service"], r["section"], r["metric"]))
    with open(DATASETS / "validation.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    bad = [r for r in out if r["difference"]]
    print(f"validation: {len(out)} totals checked, {len(bad)} differ from the sum of their categories")


if __name__ == "__main__":
    main()
