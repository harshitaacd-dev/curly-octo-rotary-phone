"""Extract NCRB State/UT-wise tables from PDF.

parse_pdf_table(path) -> (columns, records)
    columns: {col_label: header_text} where col_label is NCRB's column number ("3", "4A", ...)
    records: list of dicts state, row_type, col, value  (same shape as ncrb_tables.parse_state_table)

Works on the layout NCRB used for Crime in India 2012-2019: a row of column numbers under
the header, then one line per State/UT: "<sl> <name> <n> <n> ...", plus TOTAL rows.
Header text is assigned to the nearest column by horizontal position.
"""
import re
import pdfplumber

from ncrb_tables import clean_state, number, STATES, UTS

COLTOK = re.compile(r"^\(?(\d{1,3}[A-Z]?)\)?$")
VALTOK = re.compile(r"^(-?\d[\d,]*(\.\d+)?|@|-|\*|NA|N\.A\.)$")
SKIP_HDR = re.compile(r"^(S\.?|No\.?|Sl\.?|SL|State/UT|States?/UTs?|STATES:?)$", re.I)


def lines_of(words, tol=3):
    rows = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if rows and abs(rows[-1][0]["top"] - w["top"]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w["x0"]) for r in rows]


def find_colnum_line(lines):
    """Index of the column-number row and how many leading tokens (S.No, State) to drop.
    First pages number every column ("1 2 3 ..."); continuation pages often start at the
    first data column ("12 13 ...")."""
    for i, ln in enumerate(lines[:-1]):
        toks = [w["text"] for w in ln]
        m = [COLTOK.match(t) for t in toks]
        if len(toks) < 3 or not all(m):
            continue
        if m[0].group(1) == "1" and m[1].group(1) == "2":
            return i, 2
        nxt = " ".join(w["text"] for w in lines[i + 1])
        if re.match(r"^(STATES?|UNION TERRITORIES|UTS?)\s*:?|^\d+\s+[A-Za-z]", nxt) and int(re.match(r"\d+", toks[0]).group()) > 2:
            return i, 0
    return None, 0


def parse_page(page):
    words = page.extract_words(keep_blank_chars=False, x_tolerance=1.5, y_tolerance=2)
    lines = lines_of(words)
    ci, skip = find_colnum_line(lines)
    if ci is None:
        return {}, []
    anchors = [(COLTOK.match(w["text"]).group(1), (w["x0"] + w["x1"]) / 2) for w in lines[ci]][skip:]
    name_right = anchors[0][1] - 15  # state names end before the first data column
    # Header: lines between the table title and the column-number line.
    hdr_words = defaultdict_list()
    title_end = 0
    for i, ln in enumerate(lines[:ci]):
        if re.search(r"TABLE|During|- 20\d\d|– 20\d\d", " ".join(w["text"] for w in ln)):
            title_end = i + 1
    for ln in lines[title_end:ci]:
        for w in ln:
            if SKIP_HDR.match(w["text"]) or (w["x1"] < name_right and not COLTOK.match(w["text"])):
                continue
            xc = (w["x0"] + w["x1"]) / 2
            col = min(anchors, key=lambda a: abs(a[1] - xc))[0]
            hdr_words[col].append(w)
    columns = {}
    for col, _ in anchors:
        ws = sorted(hdr_words.get(col, []), key=lambda w: (round(w["top"] / 3), w["x0"]))
        columns[col] = re.sub(r"\s+", " ", " ".join(w["text"] for w in ws)).strip()
    records, section = [], "state"
    for ln in lines[ci + 1:]:
        toks = [w["text"] for w in ln]
        text_line = " ".join(toks)
        if re.match(r"^(STATES?|UNION TERRITORIES|UTS?)\s*:?$", text_line, re.I):
            section = "ut" if re.match(r"^(UNION|UT)", text_line, re.I) else "state"
            continue
        if re.match(r"^Cities\b", text_line, re.I):
            section = "city"  # some older tables append city rows; not State/UT data
            continue
        if section == "city":
            continue
        ws = list(ln)
        vals = []
        while ws and VALTOK.match(ws[-1]["text"]) and len(vals) < len(anchors):
            vals.insert(0, ws.pop())
        toks = [w["text"] for w in ws]
        if len(vals) == len(anchors):
            pairs = [(a[0], v["text"]) for a, v in zip(anchors, vals)]
        elif len(vals) >= 2:
            # Blank cells (e.g. no rank for total rows): place each value under the nearest column.
            pairs, used = [], set()
            for v in vals:
                xc = (v["x0"] + v["x1"]) / 2
                col = min(anchors, key=lambda a: abs(a[1] - xc))[0]
                if col in used:
                    pairs = []
                    break
                used.add(col)
                pairs.append((col, v["text"]))
            if not pairs:
                continue
        else:
            continue
        label = " ".join(toks)
        label = re.sub(r"^\d+\s+", "", label).strip()
        if not label or not re.search(r"[A-Za-z]", label):
            continue
        l = label.lower()
        if "total" in l:
            rt = "total_india" if "india" in l else ("total_uts" if re.search(r"\buts?\b|union", l) else "total_states")
        else:
            rt = section
        name = clean_state(label.title().replace(" And ", " & ") if label.isupper() else label) \
            if rt in ("state", "ut") else label.upper()
        if rt in ("state", "ut") and name not in STATES | UTS:
            continue  # city rows that some tables print after the State/UT rows
        for col, v in pairs:
            n = number(v)
            if n is None:
                continue
            records.append({"state": name, "row_type": rt, "col": col, "head": columns[col], "value": n})
    return columns, records


def defaultdict_list():
    from collections import defaultdict
    return defaultdict(list)


def parse_pdf_table(path, pages=None):
    allcols, allrecs = {}, []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages and i not in pages:
                continue
            cols, recs = parse_page(page)
            for c, h in cols.items():
                if c not in allcols or (h and len(h) > len(allcols[c])):
                    allcols[c] = h
            allrecs += recs
    # A table can repeat rows when it spans pages: keep first occurrence of (state, col).
    seen, out = set(), []
    for r in allrecs:
        k = (r["state"], r["row_type"], r["col"])
        if k not in seen:
            seen.add(k)
            out.append({**r, "head": allcols.get(r["col"], r["head"])})
    return allcols, out
