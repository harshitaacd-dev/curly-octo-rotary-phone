"""Annexure I of Lok Sabha Unstarred Question 438 (2 Dec 2025, Ministry of Home Affairs):
all-India cyber crime cases by crime head, 2014-2023, as published by NCRB.

Usage: python scripts/parse_ls438.py data/external/LS438_02122025.pdf data/clean/national_cyber_crimeheads_2014_2023.csv
"""
import csv, re, subprocess, sys

YEARS = list(range(2014, 2024))


def main(pdf, out):
    text = subprocess.run(["pdftotext", "-layout", "-f", "4", "-l", "4", pdf, "-"],
                          capture_output=True, text=True, check=True).stdout
    rows, pending = [], ""
    for line in text.splitlines():
        if "ANNEXURE-II" in line:
            break
        only_nums = re.match(r"^\s*(\d+)\s{2,}([\d\s]+)$", line)
        if only_nums and pending:  # wrapped head: name above (and below) the number row
            nums = only_nums.group(2).split()
            rows.append([pending] + [None] * (len(YEARS) - len(nums)) + [int(n) for n in nums])
            pending = ""
            continue
        m = re.match(r"^\s*(\d+|[ABC])?\s+(\D.*?)\s{2,}([\d\s]+)$", line)
        nums = m.group(3).split() if m else []
        if m and nums and not m.group(2).startswith("SL"):
            head = (pending + " " + m.group(2)).strip()
            pending = ""
            # Heads introduced in 2017 have blank cells for earlier years: right-align.
            vals = [None] * (len(YEARS) - len(nums)) + [int(n) for n in nums]
            rows.append([head] + vals)
        elif re.match(r"^\s{5,}\S", line) and not re.search(r"Crime Heads|ANNEXURE|Q\. NO|Source", line):
            if rows and re.match(r"^\s{10,}(electronic|system)", line):  # wrapped tail of the previous head
                rows[-1][0] += " " + line.strip()
            else:
                pending = line.strip()
    with open(out, "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(["crime_head"] + YEARS)
        w.writerows(rows)
    print(len(rows), "rows", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
