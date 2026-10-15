"""X (Twitter) monthly reports -> datasets/x.csv

Two layouts:
  * up to Sep 2025: grievances and URLs actioned by issue type, plus counts of
    suspension appeals (processed / overturned) and general account questions
    stated in the text;
  * from Oct 2025: total reports received and valid reports actioned, each
    broken down only as percentages by reason.
Both carry "proactive monitoring" account suspensions for child sexual
exploitation and terrorism. X says these are GLOBAL figures, not India-only.
Periods come from reports/index.csv (several PDFs misstate their own period).
"""
import re

from common import index_rows, parse_table, pdf_text, value, write

ISSUE_TYPES = [
    "Abuse / Harassment", "Ban Evasion", "Child Sexual Exploitation", "Defamation",
    "Hateful Conduct", "Illegal Activities", "Impersonation", "IP-related Infringement",
    "Misinformation / Synthetic and Manipulated Media", "Promoting Suicide or Self-Harm",
    "Terrorism / Violent Extremism", "Sensitive Adult Content", "Privacy Infringement",
    "Violent Speech", "Non-Consensual Nudity",
]


def clean(label):
    label = re.sub(r"\s*\d+$", "", label)          # footnote markers: "Illegal Activities7"
    return re.sub(r"\s+", " ", label).strip()


def issue_type(label):
    """Map a (possibly wrapped/truncated) label onto X's issue-type names."""
    lab = clean(label)
    for name in ISSUE_TYPES:
        if lab.lower() == name.lower():
            return name
    for name in ISSUE_TYPES:  # one half of a label that wrapped over two lines
        if len(lab) >= 8 and lab.lower().removeprefix("and ") in name.lower():
            return name
    return lab


def sentence_case(s):
    return s[:1].upper() + s[1:]


def between(text, start, end):
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i + len(start):j if j > 0 else len(text)]


def pct_rows(block):
    out = []
    for label, cells in parse_table(block.splitlines()):
        v, _ = value(cells[-1].replace("%", ""))
        if v is not None and "%" in cells[-1]:
            out.append((clean(label), v))
    return out


def main():
    rows = []
    for path, meta in index_rows("x").items():
        t = pdf_text(path)
        flat = re.sub(r"\s+", " ", t)
        base = dict(platform="X", service="X", period_start=meta["period_start"],
                    period_end=meta["period_end"], source_file=path)

        def add(section, category, metric, val, unit="count", service="X"):
            if val is not None:
                rows.append({**base, "service": service, "section": section, "category": category,
                             "metric": metric, "value": val, "unit": unit})

        if "Reports received:" in t:  # Oct 2025 onwards
            m = re.search(r"Reports received:\s*([\d,]+)", t)
            add("user grievances", "All", "reports received", value(m.group(1))[0])
            for cat, v in pct_rows(between(t, "selected:", "Valid Reports Actioned")):
                add("user grievances", sentence_case(re.sub(r"^Alleged\s+", "", cat)),
                    "share of reports received", v, "percent")
            m = re.search(r"Valid Reports Actioned:\s*([\d,]+)", t)
            if m:
                add("user grievances", "All", "valid reports actioned", value(m.group(1))[0])
            for cat, v in pct_rows(between(t, "Percentage of Total Actions", "Proactive Monitoring")):
                add("user grievances", sentence_case(cat), "share of valid reports actioned", v, "percent")
        else:
            block = between(t, "Issue Type", "In addition")
            for label, cells in parse_table(block.splitlines()):
                cat = issue_type(label)
                if len(cells) < 2 or cat.lower().startswith(("total number", "grievances")):
                    continue
                add("user grievances", cat, "grievances received", value(cells[-2])[0])
                add("user grievances", cat, "URLs actioned", value(cells[-1])[0])
            m = re.search(r"processed ([\d,]+) grievances which were appealing", flat)
            if m:
                add("suspension appeals", "All", "appeals processed", value(m.group(1))[0])
            m = re.search(r"overturned ([\d,]+) of (?:these|the)", flat)
            if m:
                add("suspension appeals", "All", "suspensions overturned", value(m.group(1))[0])
            elif re.search(r"(?:have not|did not) overturn(?:ed)? any|overturned none", flat):
                add("suspension appeals", "All", "suspensions overturned", 0)
            m = re.search(r"received ([\d,]+) requests related to general questions", flat)
            if m:
                add("other grievances", "General questions about accounts", "requests received",
                    value(m.group(1))[0])

        pm = between(t, "Proactive Monitoring Data", "\n\n\n")
        for label, cells in parse_table(pm.splitlines()):
            lab = clean(label)
            if lab.lower().startswith("issue") or not cells:
                continue
            cat = ("Child sexual exploitation and similar content" if "Child" in lab
                   else "Promotion of terrorism" if "Terror" in lab else lab)
            add("proactive monitoring (global, not India-only)", cat, "accounts suspended",
                value(cells[-1])[0], service="X (global)")
    write("x", rows)


if __name__ == "__main__":
    main()
