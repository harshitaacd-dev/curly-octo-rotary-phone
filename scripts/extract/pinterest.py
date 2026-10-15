"""Pinterest India monthly sections (reports/pinterest/*.html) -> datasets/pinterest.csv

Each month has two tables, "Reports" (decisions on content reported through
Pinterest's India grievance form) and "Voluntary actions" (Pinterest's own
enforcement on Indian users' content). Rows are policies; columns are the
surface (Pins, Boards, Accounts, Comments); each cell gives "N deactivated"
and sometimes "N limited distribution".
"""
import re
from html import unescape
from pathlib import Path

from common import ROOT, index_rows, num, write

ACTION_RE = re.compile(r"([\d,]+)\s*(deactivat\w*|limited distribution)", re.I)


def text(html):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def main():
    rows = []
    for path, meta in index_rows("pinterest").items():
        html = Path(ROOT / path).with_suffix(".html").read_text()
        base = dict(platform="Pinterest", period_start=meta["period_start"],
                    period_end=meta["period_end"], unit="count", source_file=path)
        # Pair each table with the <h4> heading before it.
        for m in re.finditer(r"<h4[^>]*>(.*?)</h4>(.*?)(?=<h4|$)", html, re.S):
            heading = re.sub(r"\d+$", "", text(m.group(1))).strip()  # drop footnote marker
            section = {"Reports": "user reports (grievance form)",
                       "Voluntary actions": "voluntary actions"}.get(heading, heading.lower())
            table = re.search(r"<table.*?</table>", m.group(2), re.S)
            if not table:
                continue
            head = [text(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", table.group(0), re.S)]
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(0), re.S):
                cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                if not cells:
                    continue
                policy = re.sub(r"[\s\d¹²³⁴]+$", "", text(cells[0]))  # footnote markers
                for surface, cell in zip(head[1:], cells[1:]):
                    for n, action in ACTION_RE.findall(text(cell)):
                        action = "deactivated" if action.lower().startswith("deactiv") else "limited distribution"
                        rows.append({**base, "service": surface, "section": section,
                                     "category": policy, "metric": action, "value": num(n)})
    write("pinterest", rows)


if __name__ == "__main__":
    main()
