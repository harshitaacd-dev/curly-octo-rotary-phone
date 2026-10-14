"""Parse NCRB 'Crime in India' State/UT-wise Excel tables into long records.

parse_state_table(path) -> list of dicts with keys
    state, row_type ('state' | 'ut' | 'total_states' | 'total_uts' | 'total_india'),
    col (NCRB column number), head (flattened multi-row header), value.
"""
import re
import openpyxl

HEADER_START = re.compile(r"^\s*(SL|S\.?\s*No\.?)\s*$", re.I)
COLNUM = re.compile(r"^\s*\[?\(?(\d+)\)?\]?\s*$")
SECTION = re.compile(r"^\s*(STATES?|UNION TERRITORIES|UTS?)\s*:?\s*$", re.I)
STATE_FIX = {
    "Andrha Pradesh": "Andhra Pradesh", "A & N Islands": "A&N Islands", "A&N Island": "A&N Islands",
    "Andaman & Nicobar Islands": "A&N Islands", "Delhi UT": "Delhi", "Delhi (UT)": "Delhi",
    "D & N Haveli": "D&N Haveli", "Daman & Diu": "Daman & Diu", "Jammu And Kashmir": "Jammu & Kashmir",
    "Orissa": "Odisha", "Pondicherry": "Puducherry", "Uttaranchal": "Uttarakhand",
    "D&N Haveli and Daman & Diu": "D&N Haveli and Daman & Diu",
    "Dadra & Nagar Haveli and Daman & Diu": "D&N Haveli and Daman & Diu",
    "D & N Haveli and Daman & Diu": "D&N Haveli and Daman & Diu",
    "Dadra & Nagar Haveli": "D&N Haveli", "UT of Delhi": "Delhi", "Delhi UT": "Delhi",
    "A & N Islands": "A&N Islands", "Andaman & Nicobar Islands": "A&N Islands",
}
UTS = {"A&N Islands", "Chandigarh", "D&N Haveli", "Daman & Diu", "D&N Haveli and Daman & Diu",
       "Delhi", "Lakshadweep", "Puducherry", "Ladakh"}  # plus Jammu & Kashmir from 2019


def text(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return re.sub(r"\s+", " ", str(v).replace("​", "").replace("\xa0", " ")).strip()


def number(v):
    s = text(v).replace(",", "").rstrip("*#@$").strip()
    if s in ("", "-", "NA", "N.A.", "N.A", "--"):
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f == int(f) else f


def clean_state(name):
    name = re.sub(r"[*#@$+]+$|\s*\(?\d\)?$", "", text(name)).strip()
    name = re.sub(r"\s*&\s*", " & ", name)
    return STATE_FIX.get(name, name)


def read_rows(path):
    """All cells of the first sheet as text, merged ranges filled with their value."""
    if path.lower().endswith(".xls"):
        import xlrd
        sh = xlrd.open_workbook(path, formatting_info=True).sheet_by_index(0)
        rows = [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
        for r0, r1, c0, c1 in sh.merged_cells:
            for r in range(r0, r1):
                for c in range(c0, c1):
                    rows[r][c] = rows[r0][c0]
        return rows
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    for rng in ws.merged_cells.ranges:
        v = ws.cell(rng.min_row, rng.min_col).value
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                if r - 1 < len(rows) and c - 1 < len(rows[r - 1]):
                    rows[r - 1][c - 1] = v
    return rows


def row_type(label, section):
    l = label.lower()
    if "total" in l:
        if "india" in l:
            return "total_india"
        return "total_uts" if re.search(r"\buts?\b|union", l) else "total_states"
    return section


def parse_state_table(path):
    rows = read_rows(path)
    h0 = next(i for i, r in enumerate(rows) if r and HEADER_START.match(text(r[0])))
    # Column-number row: first row after the header whose first cell is 1 / [1] and second 2 / [2].
    h1 = next((i for i in range(h0 + 1, min(h0 + 12, len(rows)))
               if len(rows[i]) > 1 and COLNUM.match(text(rows[i][0])) and COLNUM.match(text(rows[i][1]))
               and int(COLNUM.match(text(rows[i][0])).group(1)) == 1
               and int(COLNUM.match(text(rows[i][1])).group(1)) == 2), None)
    width = max(len(r) for r in rows)
    rows = [list(r) + [None] * (width - len(r)) for r in rows]
    hdr_end = h1 if h1 is not None else h0 + 1
    data_start = (h1 + 1) if h1 is not None else h0 + 1
    # Page blocks: each starts at a column whose header cell is SL / S. No.
    starts = [c for c in range(width) if HEADER_START.match(text(rows[h0][c]))]
    cols = {}
    for bi, s in enumerate(starts):
        end = starts[bi + 1] if bi + 1 < len(starts) else width
        for c in range(s + 2, end):
            parts = []
            for r in range(h0, hdr_end):
                t = text(rows[r][c])
                if t and (not parts or parts[-1] != t):
                    parts.append(t)
            if not parts:
                continue
            num = COLNUM.match(text(rows[h1][c])) if h1 is not None else None
            key = int(num.group(1)) if num else c + 1
            head = " > ".join(parts)
            # NCRB occasionally reuses a column number for two different heads; keep both.
            if any(k[0] == key and v[2] == head for k, v in cols.items()):
                continue
            cols[(key, len(cols))] = (s + 1, c, head)
    out, section = [], "state"
    for r in rows[data_start:]:
        first = text(r[0])
        if SECTION.match(first):
            section = "ut" if re.match(r"\s*(UNION|UT)", first, re.I) else "state"
            continue
        if first.startswith(("●", "+", "Note", "Source", "*", "#")) and not text(r[1]):
            continue
        for key, (state_col, c, head) in cols.items():
            label = text(r[state_col])
            if not label or SECTION.match(label):
                continue
            if not (COLNUM.match(text(r[state_col - 1])) or "total" in label.lower()):
                continue
            v = number(r[c])
            if v is None:
                continue
            rt = row_type(label, section)
            out.append({"state": clean_state(label) if rt in ("state", "ut") else label.upper(),
                        "row_type": rt, "col": key[0], "head": head, "value": v})
    return out
