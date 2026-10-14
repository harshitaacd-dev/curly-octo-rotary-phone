"""Build cleaned State/UT-level datasets from the downloaded NCRB tables.

Usage: python scripts/build_state_datasets.py data/ncrb data/clean

Outputs (all one row per state/UT x year unless noted):
  state_women_cyber_panel.csv     totals, rates and key crime heads for crimes
                                  against women and cyber crimes
  state_cyber_sexual_abusive.csv  cyber crimes that are sexual or abusive in nature
  state_crimeheads_long.csv       every crime head parsed, long format (one row per
                                  state x year x table x head x measure), with the
                                  harmonised key where one applies
"""
import csv, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from ncrb_tables import parse_state_table, read_rows, text, number, clean_state, UTS  # noqa: E402
from ncrb_pdf import parse_pdf_table  # noqa: E402

AGG = {"total_states": "Total (States)", "total_uts": "Total (UTs)", "total_india": "All India"}


# ---------------------------------------------------------------- catalog helpers
def find(catalog, year, title_rx, fmt=("xlsx", "xls"), exclude=None, data_year=None):
    hits = [r for r in catalog if int(r["year"]) == year and r["format"] in fmt
            and r["status"] in ("ok", "exists") and re.search(title_rx, r["title"], re.I)
            and not (exclude and re.search(exclude, r["title"], re.I))]
    for r in hits:
        if title_year_ok(os.path.join(SRC, r["file"]), data_year or year):
            return r
        print(f"skipping {r['file']}: its title is for a different year", file=sys.stderr)
    return None


def title_year_ok(path, year):
    """False when the table's own title names a different year (NCRB's 2019 page, for
    example, links the 2020 crime-head file)."""
    head = " ".join(text(c) for r in read_rows(path)[:4] for c in r[:3])
    ranges = [(int(a), int(b)) for a, b in re.findall(r"(20\d\d)\s*[-–]\s*(20\d\d)", head)]
    years = {int(y) for y in re.findall(r"\b(20[0-2]\d)\b", head)}
    return not years or year in years or any(a <= year <= b for a, b in ranges)


def state_name(rec):
    return AGG.get(rec["row_type"]) or rec["state"]


# ---------------------------------------------------------------- crime-head harmonisation
MEASURES = {"I": "cases", "Total": "cases", "IPC": "cases_ipc", "BNS": "cases_bns",
            "V": "victims", "R": "rate"}

WOMEN_KEYS = [  # matched against the head path with the measure removed
    ("total_caw", r"^Total Crimes? against Women"),
    ("total_ipc_caw", r"^Total (IPC|IPC/BNS) Crimes against Women"),
    ("total_sll_caw", r"^Total SLL Crimes against Women"),
    ("murder_with_rape", r"^Murder with Rape"),
    ("sexual_intercourse_deceit_bns69", r"^Sexual Intercourse by employing deceitful"),
    ("rape", r"^Rape\b([^>]*> Rape \(Total[^>]*)?$"),
    ("rape_women_18plus", r"^Rape\b.*> [Aa]\) Women"),
    ("rape_girls_u18", r"^Rape\b.*> [Bb]\) Girls"),
    ("attempt_rape", r"^Attempt to [Cc]ommit Rape([^>]*> Attempt to [Cc]ommit Rape \(Total[^>]*)?$"),
    ("dowry_deaths", r"^Dowry Deaths"),
    ("abetment_suicide_women", r"^Abetment (to|of) [Ss]uicides? of [Ww]omen"),
    ("acid_attack", r"^Acid Attack"),
    ("attempt_acid_attack", r"^Attempt to Acid Attack"),
    ("cruelty_husband_relatives", r"^Cruelty by Husband"),
    ("kidnap_for_marriage", r"compel her for marriage[^>]*> (K&A of Women|Kidnapping or abducting or inducing Women) to compel her for marriage \(To"),
    ("kidnap_abduction_women", r"^Kidnapping & Abduction of Women( > Kidnapping & Abduction of Women \(Total[^>]*)?$"),
    ("assault_modesty_354", r"^Assault on Women with [Ii]ntent to [Oo]utrage her Modesty([^>]*> Assault on Women with [Ii]ntent to [Oo]utrage her Modesty \(Total[^>]*)?$"),
    ("sexual_harassment_354a", r"^Sexual Harassment[^>]*> Sexual Harassment \(Total"),
    ("disrobe_354b", r"^Assault or Use of Criminal Force with intent to disrobe[^>]*> [^>]*\(Total"),
    ("voyeurism_354c", r"^Voyeurism[^>]*> Voyeurism \(Total"),
    ("stalking_354d", r"^Stalking[^>]*> Stalking \(Total"),
    ("insult_modesty_509", r"^Insult to the Modesty of Women([^>]*> Insult to the Modesty of Women \(Total[^>]*)?$"),
    ("human_trafficking_370", r"^Human Trafficking"),
    ("procuration_minor_girls", r"Procuration of Minor Girls"),
    ("importation_girls", r"Importation of Girls"),
    ("selling_girls", r"^Selling of (Minor )?Girls"),
    ("buying_girls", r"^Buying of (Minor )?Girls"),
    ("dowry_prohibition_act", r"^Dowry Prohibition Act"),
    ("immoral_traffic_act", r"^Immoral Traffic(.*\(Total[^>]*)?$"),
    ("domestic_violence_act", r"^Protection of Women from Domestic Violence"),
    ("cyber_women_centric", r"^Cyber Crimes/Information Technology Act.*\(Total"),
    ("cyber_women_sexually_explicit_67a_67b", r"^Cyber Crimes/Information Technology Act.*> [Aa]\) Publishing or Transmitting"),
    ("pocso_girls", r"^Protection of Children from Sexual.*(\(Total|POCSO Act \(Total)"),
    ("indecent_representation_act", r"^Indecent Representation"),
    ("sati_act", r"^Commission of Sati"),
]

CYBER_KEYS = [  # matched against the last segment of the head path
    ("cyber_total", r"^Total Cyber Crimes"),
    ("it_act_total", r"^Total Offences under I\.?\s?T\.? Act"),
    ("ipc_total", r"^Total Offences under (IPC|IPC/BNS)$"),
    ("sll_total", r"^Total (Offences under SLL|SLL Offences)"),
    ("it65_tampering", r"^Tampering computer source"),
    ("it66_computer_related_total", r"^Computer Related Offences( \(Total\)| \(Section 66 and Section 66[AB] to 66E\))?$"),
    ("it66c_identity_theft", r"Identity Theft"),
    ("it66d_cheating_personation", r"Cheating by personation"),
    ("it66e_violation_privacy", r"Violation of Privacy"),
    ("it67_total", r"^Publication/ ?[Tt]ransmission of [Oo]bscene ?/ ?[Ss]exually [Ee]xplicit (act in electronic form( \(Total\))?|Content \(Sec 67 And Sec 67A to 67C\))$"),
    ("it67_obscene", r"Publishing or transmitting obscene material"),
    ("it67a_sexually_explicit", r"material containing Sexually explicit act"),
    ("it67b_child_sexual_material", r"material depicting children in Sexually explicit"),
    ("it67c_retention", r"Preservation and retention"),
    ("it67_other", r"Other (sub- ?s|S)ections (of )?(Sec\. )?67"),
    ("it72_breach_privacy", r"^Breach of Confidentiality"),
    ("abetment_suicide_online", r"^Abetment of Suicide \(Online\)"),
    ("cyber_stalking_bullying", r"^Cyber Stalking/ ?Bullying"),
    ("sexual_intercourse_deceit_bns69", r"^Sexual Intercourse by Deceitful"),
    ("defamation_morphing", r"^Defamation/ ?Morphing"),
    ("fake_profile", r"^Fake Profile"),
    ("cyber_blackmail_threat", r"^Cyber Blackmailing"),
    ("fake_news", r"^Fake News"),
    # Before 2017 NCRB's cyber "fraud" head was criminal breach of trust (Sec 406-409) only;
    # from 2017 it is Sec 420 r/w 465, 468-471 fraud. Keep them apart.
    ("fraud_total", r"^(Fraud\b(?!.*>)|Fraud \(Total\))"),
    ("cbt_fraud", r"^Criminal Breach of Trust/Fraud"),
    ("cheating", r"^Cheating( \(Sec|$)"),
    ("forgery", r"^Forgery"),
    ("data_theft", r"^Data [Tt]heft"),
]

CYBER_WOMEN_KEYS = [  # Table 9A.10, Cyber Crimes against Women
    ("women_cyber_blackmail_threat", r"^Cyber Blackmailing"),
    ("women_cyber_pornography_obscene", r"^Cyber Pornography"),
    ("women_cyber_stalking_bullying", r"^Cyber Stalking"),
    ("women_sexual_intercourse_deceit", r"^Sexual Intercourse by Deceit"),
    ("women_defamation_morphing", r"^Defamation"),
    ("women_fake_profile", r"^Fake Profile"),
    ("women_other_cyber", r"^Other"),
    ("women_cyber_total", r"^Total"),
]
CYBER_CHILD_KEYS = [  # Table 9A.11, Cyber Crimes against Children
    ("children_cyber_blackmail_harassment", r"^Cyber Blackmailing"),
    ("children_fake_profile", r"^Fake Profile"),
    ("children_cyber_pornography_csam", r"^Cyber Pornography"),
    ("children_cyber_stalking_bullying", r"^Cyber Stalking"),
    ("children_online_games_gaming_apps", r"(Online Games|Gaming Apps)"),
    ("children_other_cyber", r"^Other"),
    ("children_cyber_total", r"^Total"),
]


def match_key(keys, s):
    for k, rx in keys:
        if re.search(rx, s):
            return k
    return None


def split_measure(head):
    parts = head.split(" > ")
    if len(parts) > 1 and parts[-1] in MEASURES:
        return " > ".join(parts[:-1]), MEASURES[parts[-1]]
    return head, "cases"


# ---------------------------------------------------------------- readers
class Store:
    def __init__(self):
        self.long = []  # rows for state_crimeheads_long.csv
        self.panel = defaultdict(dict)  # (state, year) -> {var: value}
        self.src = defaultdict(set)

    def add(self, year, state, category, table, head, measure, key, value, source):
        self.long.append({"year": year, "state": state, "category": category, "table": table,
                          "crime_head": head, "measure": measure, "key": key or "",
                          "value": value, "source_file": source})

    def put(self, year, state, var, value, source, overwrite=False):
        cell = self.panel[(state, year)]
        if var not in cell or overwrite:
            cell[var] = value
        self.src[var].add(f"{year}:{source}")


def read_summary(store, cat, year, rec, prefix):
    """Tables 3A.1 / 9A.1: three years of cases plus population, rate, chargesheeting rate."""
    f = rec["file"]
    for r in parse_state_table(os.path.join(SRC, f)):
        h, st = r["head"], state_name(r)
        if re.fullmatch(r"\d{4}", h):
            y = int(h)
            # Each report's own year wins. Earlier-year columns only fill 2015-2016, which have
            # no Excel report of their own (they also carry later boundary changes, e.g. the
            # 2020 D&N Haveli + Daman & Diu merger, back onto earlier years).
            if y == year or y < 2017:
                store.put(y, st, f"{prefix}_cases", r["value"], f, overwrite=(y == year))
        elif "population" in h.lower():
            store.put(year, st, f"{prefix}_population_lakh", r["value"], f, overwrite=True)
        elif h.lower().startswith("rate of total"):
            store.put(year, st, f"{prefix}_rate", r["value"], f, overwrite=True)
        elif "chargesheeting" in h.lower():
            store.put(year, st, f"{prefix}_chargesheeting_rate", r["value"], f, overwrite=True)


def read_heads(store, cat, year, rec, table, keys, use_last_segment, panel_prefix):
    f = rec["file"]
    for r in parse_state_table(os.path.join(SRC, f)):
        path, measure = split_measure(r["head"])
        probe = path.split(" > ")[-1] if use_last_segment else path
        key = match_key(keys, probe)
        st = state_name(r)
        store.add(year, st, cat, table, path, measure, key, r["value"], f)
        if key and measure in ("cases", "victims", "rate"):
            var = f"{panel_prefix}{key}" + ("" if measure == "cases" else f"_{measure}")
            store.put(year, st, var, r["value"], f, overwrite=True)


def read_women_2001_2015(store, rec):
    """2015 edition: state blocks, crime heads x years 2001-2015 (cases)."""
    f = rec["file"]
    rows = read_rows(os.path.join(SRC, f))
    state, years, sums = None, {}, defaultdict(float)
    for r in rows:
        a, b = text(r[0]), text(r[1]) if len(r) > 1 else ""
        m = re.search(r"Crime against Women in (.+?) During", a)
        if m:
            state = m.group(1)
            state = AGG.get({"Total (All India)": "total_india", "All India": "total_india",
                             "Total (States)": "total_states", "Total (UTs)": "total_uts"}.get(state, ""), clean_state(state))
            continue
        if a.upper() == "SL":
            years = {c: int(text(v)) for c, v in enumerate(r) if re.fullmatch(r"\d{4}", text(v))}
            continue
        if state and re.fullmatch(r"\d+", a) and b:
            key = match_key(WOMEN_KEYS, b)
            for c, y in years.items():
                v = number(r[c])
                if v is None or y < 2012:
                    continue
                store.add(y, state, "women", "CII2015 yearwise", b, "cases", key, v, f)
                if key:
                    var = f"women_{key}" if key != "total_caw" else "women_cases"
                    store.put(y, state, var, v, f, overwrite=False)
                    group = "Total (UTs)" if state in UTS else "Total (States)"
                    sums[(y, group, var)] += v
                    sums[(y, "All India", var)] += v
    # This file has no aggregate rows; derive them from the states so totals match.
    for (y, group, var), v in sums.items():
        store.put(y, group, var, v, f + " (sum of states)", overwrite=True)


def read_cyber_2014(store, rec):
    """2015 edition file with State/UT x cyber crime head, cases reported in 2014."""
    f = rec["file"]
    rows = read_rows(os.path.join(SRC, f))
    hdr = next(i for i, r in enumerate(rows) if text(r[0]).upper() == "SL")
    heads = {}
    for c in range(len(rows[hdr])):
        lab = text(rows[hdr][c])
        if lab and lab.upper() not in ("SL", "STATE/UT"):
            grp = text(rows[hdr - 1][c])
            heads[c] = f"{grp} > {lab}" if grp else lab
    state_cols = [c for c in range(len(rows[hdr])) if text(rows[hdr][c]).upper() == "STATE/UT"]
    for r in rows[hdr + 1:]:
        for c, head in heads.items():
            sc = max(s for s in state_cols if s < c)
            lab = text(r[sc])
            v = number(r[c]) if c < len(r) else None
            if not lab or v is None:
                continue
            l = lab.lower()
            st = ("All India" if "india" in l else "Total (UTs)" if "ut" in l else "Total (States)") \
                if "total" in l else clean_state(lab)
            key = match_key(CYBER_KEYS, head.split(" > ")[-1])
            store.add(2014, st, "cyber", "CII2015 cyber 2014", head, "cases", key, v, f)
            if key:
                store.put(2014, st, f"cyber_{key}", v, f, overwrite=True)
    # No grand-total column in this file: total = IT Act + IPC + SLL.
    for (st, y), cell in store.panel.items():
        if y == 2014 and all(k in cell for k in ("cyber_it_act_total", "cyber_ipc_total", "cyber_sll_total")):
            store.put(2014, st, "cyber_cases",
                      cell["cyber_it_act_total"] + cell["cyber_ipc_total"] + cell["cyber_sll_total"], f)


# ---------------------------------------------------------------- PDF-only years
# Column maps written from the printed headers: NCRB column number -> (key, label).
# For crimes against women each key column is "I" (cases); "V" and "R" follow it.
WOMEN_2016_3A2 = {
    "3": ("dowry_deaths", "Dowry Deaths (Sec.304B IPC)"),
    "6": ("abetment_suicide_women", "Abetment of Suicide of Women (Sec.306 IPC)"),
    "9": (None, "Causing miscarriage without women's consent (Sec.313 IPC)"),
    "12": (None, "Deaths caused by act done with intent to cause miscarriage (Sec.314 IPC)"),
    "15": ("acid_attack_incl_attempt", "Acid Attack (Sec. 326A IPC) & Attempt to Acid Attack (Sec. 326B IPC)"),
    "18": ("cruelty_husband_relatives", "Cruelty by Husband or his relatives (Sec. 498A IPC)"),
    "21": ("kidnap_abduction_women", "Kidnapping & Abduction of Women (Total)"),
    "21A": (None, "Kidnapping & Abduction (Sec.363 IPC)"),
    "21B": (None, "Kidnapping & Abduction in order to Murder (Sec.364 IPC)"),
    "21C": (None, "Kidnapping for Ransom (Sec.364A IPC)"),
    "21D": ("kidnap_for_marriage", "Kidnapping & Abduction of Women to compel her for Marriage (Sec.366 IPC)"),
    "21E": (None, "Other Kidnapping & Abduction (Female) (Sec.363A, 365, 366A, 366B, 367, 368, 369 IPC)"),
    "24": ("human_trafficking_370", "Human Trafficking (Female) (Sec.370 & 370A IPC)"),
    "27": ("rape", "Rape (Total)"),
    "27A": (None, "Rape (Sec.376 IPC)"),
    "27B": (None, "Gang Rape (Sec.376D IPC)"),
    "27C": (None, "Custodial Rape (Sec.376C IPC)"),
    "30": ("attempt_rape", "Attempt to Commit Rape (Sec.376/511 IPC)"),
    "33": (None, "Unnatural Offences (Sec.377 IPC)"),
    "36": ("assault_modesty_354", "Assault on Women with Intent to Outrage her Modesty (Total)"),
    "36A": (None, "Assault on Women (Sec.354 IPC)"),
    "36B": ("sexual_harassment_354a", "Sexual Harassment (Sec.354A IPC)"),
    "36C": ("disrobe_354b", "Assault or Use of Criminal Force to Women with Intent to Disrobe (Sec.354B IPC)"),
    "36D": ("voyeurism_354c", "Voyeurism (Sec.354C IPC)"),
    "36E": ("stalking_354d", "Stalking (Sec.354D IPC)"),
    "39": ("insult_modesty_509", "Insult to the Modesty of Women (Sec.509 IPC)"),
    "42": ("total_ipc_caw", "Total IPC Crimes against Women"),
    "45": ("dowry_prohibition_act", "Dowry Prohibition Act, 1961"),
    "48": ("immoral_traffic_act", "Immoral Traffic (Prevention) Act 1956 (Total)"),
    "48A": (None, "ITP Act - Procuring/Inducing a Person for sake of Prostitution (Sec 5)"),
    "48B": (None, "ITP Act - Detaining a Person in Premises where prostitution is carried on (Sec 6)"),
    "48C": (None, "ITP Act - Prostitution in the Vicinity of Public Places (Sec 7)"),
    "48D": (None, "ITP Act - Seducing or Soliciting for Prostitution (Sec 8)"),
    "48E": (None, "ITP Act - Other Sections"),
    "51": ("domestic_violence_act", "Protection of Women from Domestic Violence Act, 2005"),
    "54": ("cyber_women_sexually_explicit_67a_67b", "Publishing or Transmitting of Material containing Sexually Explicit Act (Sec 67A IT Act)"),
    "57": ("indecent_representation_act", "Indecent Representation of Women (Prohibition) Act, 1986"),
    "60": ("total_sll_caw", "Total SLL Crimes against Women"),
    "63": ("total_caw", "Total Crime against Women (IPC+SLL)"),
}
CYBER_2016 = {  # Tables 9A.2(i)-(iii), 2016
    "9A.2(i)": {
        "3": ("it65_tampering", "Tampering Computer Source Documents (Sec 65)"),
        "4": ("it66_computer_related_total", "Computer Related Offences (Sec 66 and 66B-E) (Total)"),
        "4A": (None, "Computer Related Offences - Under Section 66"),
        "4B": (None, "Computer Related Offences - Under Section 66B"),
        "4C": ("it66c_identity_theft", "Identity Theft (Sec 66C)"),
        "4D": ("it66d_cheating_personation", "Cheating by Personation using Computer Resource (Sec 66D)"),
        "4E": ("it66e_violation_privacy", "Violation of Privacy (Sec 66E)"),
        "5": (None, "Cyber Terrorism (Sec 66F)"),
        "6": ("it67_total", "Publication/Transmission of Obscene/Sexually Explicit Act in Electronic Form (Total)"),
        "6A": ("it67a_sexually_explicit", "Under Section 67A"),
        "6B": ("it67b_child_sexual_material", "Under Section 67B"),
        "6C": ("it67c_retention", "Under Section 67C"),
        "7": ("it72_breach_privacy", "Breach of Confidentiality/Privacy (Sec 72) & Disclosure of Information in Breach of Lawful Contract (Sec 72A)"),
        "8": (None, "Other Cyber Crimes (IT Act)"),
        "9": ("it_act_total", "Total Cyber Crimes under IT Act"),
    },
    "9A.2(ii)": {
        "3": ("data_theft", "Data Theft (Sec 379 to 381 IPC)"),
        "4": ("cbt_fraud", "Criminal Breach of Trust/Fraud (Sec 406, 408, 409 IPC) (Total)"),
        "4A": (None, "Criminal Breach of Trust/Fraud - Debit Card/Credit Card"),
        "4B": (None, "Criminal Breach of Trust/Fraud - Others"),
        "5": ("cheating", "Cheating (Sec 420 IPC)"),
        "6": ("forgery", "Forgery (Sec 465-468, 471 & 477A IPC)"),
        "7": (None, "Counterfeiting (Sec 489A to 489E IPC)"),
        "8": (None, "Fabrication of False Evidence/Destruction of Electronic Records (Sec 193, 204 IPC)"),
        "9": (None, "Other IPC Crimes"),
        "10": ("ipc_total", "Total Cyber Crimes under IPC"),
    },
    "9A.2(iii)": {
        "3": (None, "Copy Right Act"),
        "4": (None, "Trade Marks Act, 1999"),
        "5": (None, "Other SLL Offences"),
        "6": ("sll_total", "Total Cyber Crimes under SLL"),
        "10": ("cyber_total", "Total Cyber Crimes"),
    },
}
CYBER_2013 = {
    "18.6": {
        "3": ("it65_tampering", "Tampering Computer Source Document (Sec 65)"),
        "4": (None, "Hacking - Loss/damage to computer resource/utility (Sec 66(1))"),
        "5": (None, "Hacking (Sec 66(2))"),
        "6": ("it67_total", "Obscene Publication/Transmission in Electronic Form (Sec 67)"),
        "7": (None, "Failure of compliance/orders of Certifying Authority (Sec 68)"),
        "8": (None, "Failure to assist in decrypting information intercepted by Govt. Agency (Sec 69)"),
        "9": (None, "Un-authorised access/attempt to access protected computer system (Sec 70)"),
        "10": (None, "Obtaining Licence or Digital Signature by misrepresentation (Sec 71)"),
        "11": (None, "Publishing false Digital Signature certificate (Sec 73)"),
        "12": (None, "Fraud Digital Signature (Sec 74)"),
        "13": ("it72_breach_privacy", "Breach of confidentiality/privacy (Sec 72)"),
        "14": (None, "Others (IT Act)"),
        "15": ("it_act_total", "Total (IT Act)"),
    },
    "18.7": {
        "3": (None, "Offences by/Against Public Servant"),
        "4": (None, "False electronic evidence"),
        "5": (None, "Destruction of electronic evidence"),
        "6": ("forgery", "Forgery"),
        "7": ("cbt_fraud", "Criminal Breach of Trust/Fraud"),
        "8": (None, "Counterfeiting - Property mark"),
        "9": (None, "Counterfeiting - Tampering"),
        "10": (None, "Counterfeiting - Currency/Stamps"),
        "11": ("ipc_total", "Total (IPC)"),
    },
}


def shift(col, k):
    m = re.match(r"(\d+)([A-Z]?)$", col)
    return f"{int(m.group(1)) + k}{m.group(2)}"


def read_pdf_mapped(store, cat, year, path, table, colmap, prefix, triplets=False):
    """Read a PDF table whose columns are described by colmap {col: (key, label)}."""
    _, recs = parse_pdf_table(os.path.join(SRC, path))
    lookup = {}
    for col, (key, label) in colmap.items():
        if triplets:
            for k, measure in ((0, "cases"), (1, "victims"), (2, "rate")):
                lookup[shift(col, k)] = (key, label, measure)
        else:
            lookup[col] = (key, label, "cases")
    n = 0
    for r in recs:
        if r["col"] not in lookup:
            continue
        key, label, measure = lookup[r["col"]]
        st = state_name(r)
        store.add(year, st, cat, table, label, measure, key, r["value"], path)
        if key:
            var = f"{prefix}{key}" + ("" if measure == "cases" else f"_{measure}")
            store.put(year, st, var, r["value"], path, overwrite=False)
        n += 1
    return n


def read_pdf_with_excel_heads(store, cat, year, path, template, table, keys, prefix):
    """PDF whose layout matches another year's Excel table: take headers from the template."""
    heads = {}
    for r in parse_state_table(os.path.join(SRC, template)):
        heads.setdefault(str(r["col"]), r["head"])
    _, recs = parse_pdf_table(os.path.join(SRC, path))
    for r in recs:
        if r["col"] not in heads:
            continue
        p, measure = split_measure(heads[r["col"]])
        key = match_key(keys, p)
        st = state_name(r)
        store.add(year, st, cat, table, p, measure, key, r["value"], path)
        if key and measure in ("cases", "victims", "rate"):
            store.put(year, st, f"{prefix}{key}" + ("" if measure == "cases" else f"_{measure}"),
                      r["value"], path, overwrite=False)


def read_pdf_years(store, path, colyears, prefix, table):
    """Multi-year totals tables (e.g. 18.1: IT Act and IPC for 2012 & 2013)."""
    _, recs = parse_pdf_table(os.path.join(SRC, path))
    for r in recs:
        if r["col"] in colyears:
            y, var = colyears[r["col"]]
            st = state_name(r)
            store.add(y, st, "cyber", table, var, "cases", var, r["value"], path)
            store.put(y, st, f"{prefix}{var}", r["value"], path, overwrite=False)


def read_354_from_district_files(store, catalog):
    """Sec 354A-D (sexual harassment, disrobing, voyeurism, stalking) for 2014-2015.
    The state tables only report Sec 354 as a whole for these years; the district-wise
    files split it, and their district rows add up to each state's total row."""
    from clean_district import parse
    heads = [("sexual_harassment_354a", r"^Sexual Harassment$"),
             ("disrobe_354b", r"^Assault on women with intent to Disrobe$"),
             ("voyeurism_354c", r"^Voyeurism$"),
             ("stalking_354d", r"^Stalking$")]
    for year in (2014, 2015):
        rec = find(catalog, year, r"District-wise Crimes committed against Women")
        if not rec:
            continue
        cols, _, totals = parse(os.path.join(SRC, rec["file"]))
        sums = defaultdict(float)
        for raw_state, vals in totals.items():
            st = clean_state(raw_state)
            for c, head in cols.items():
                key = match_key(heads, head)
                if key is None or vals.get(c) is None:
                    continue
                store.add(year, st, "women", "district-wise (state totals)", head, "cases", key, vals[c], rec["file"])
                store.put(year, st, f"women_{key}", vals[c], rec["file"], overwrite=False)
                sums[("Total (UTs)" if st in UTS else "Total (States)", key)] += vals[c]
                sums[("All India", key)] += vals[c]
        for (group, key), v in sums.items():
            store.put(year, group, f"women_{key}", v, rec["file"] + " (sum of states)", overwrite=False)


NATIONAL_KEYS = {
    "Total Offences under I.T. Act": "cyber_it_act_total",
    "Total Offences under IPC": "cyber_ipc_total",
    "Total Offences under SLL": "cyber_sll_total",
    "Publication/transmission of obscene / sexually explicit act in electronic form": "cyber_it67_total",
    "Computer Related Offences": "cyber_it66_computer_related_total",
    "Data theft": "cyber_data_theft",
    "Cheating": "cyber_cheating",
    "Forgery": "cyber_forgery",
}


def read_national_cyber_heads(store, path):
    """All-India cyber crime heads (Lok Sabha USQ 438, 2025). Only fills All India cells that
    are still empty, which in practice is 2015: NCRB did not publish that year's crime heads
    by State."""
    if not os.path.exists(path):
        return
    for row in csv.DictReader(open(path, encoding="utf8")):
        var = NATIONAL_KEYS.get(row["crime_head"])
        for y in range(2014, 2024):
            v = number(row.get(str(y)))
            if v is None:
                continue
            store.add(y, "All India", "cyber", "LS USQ 438 (2025) Annexure I", row["crime_head"], "cases",
                      var.replace("cyber_", "") if var else "", v, os.path.basename(path))
            if var:
                store.put(y, "All India", var, v, os.path.basename(path), overwrite=False)


def read_pdf_only_years(store, catalog):
    def pdf(year, rx):
        hits = [r for r in catalog if int(r["year"]) == year and r["format"] == "pdf"
                and r["status"] in ("ok", "exists") and re.search(rx, r["title"], re.I)]
        return hits[0]["file"] if hits else None

    # 2019 crime heads (the Excel link serves 2020 data). Same layout as 2018 Excel.
    tmpl = find(catalog, 2018, r"Crimes? Against Women.*Crime Head-wise & States?/UT")
    p2019 = "2019/women/Table-3A.2_2.pdf"
    if tmpl and os.path.exists(os.path.join(SRC, p2019)):
        read_pdf_with_excel_heads(store, "women", 2019, p2019, tmpl["file"], "3A.2", WOMEN_KEYS, "women_")
    f = pdf(2016, r"^Incidence \(Crime Head-wise & States/UT-wise\) -- 2016")
    if f:
        read_pdf_mapped(store, "women", 2016, f, "3A.2", WOMEN_2016_3A2, "women_", triplets=True)
    for table, rx in (("9A.2(i)", r"IT Act Cases"), ("9A.2(ii)", r"^9A\.2\(ii\)"), ("9A.2(iii)", r"^9A\.2\(iii\)")):
        f = pdf(2016, rx)
        if f:
            read_pdf_mapped(store, "cyber", 2016, f, table, CYBER_2016[table], "cyber_")
    f = pdf(2016, r"Cyber Crimes Incidence & Crime Rate \(State/UT-wise\)")
    if f:
        _, recs = parse_pdf_table(os.path.join(SRC, f))
        for r in recs:
            var = {"8": "cyber_population_lakh", "9": "cyber_rate"}.get(r["col"])
            if var:
                store.put(2016, state_name(r), var, r["value"], f, overwrite=False)
    f = pdf(2013, r"Cases Registered under I\.T\. Act \(State")
    if f:
        read_pdf_mapped(store, "cyber", 2013, f, "18.6", CYBER_2013["18.6"], "cyber_")
    f = pdf(2013, r"Cases Registered under IPC \(State")
    if f:
        read_pdf_mapped(store, "cyber", 2013, f, "18.7", CYBER_2013["18.7"], "cyber_")
    f = pdf(2013, r"Incidence of Cases Registered under Cyber Crimes \(State")
    if f:  # 2012 & 2013 totals: IT Act (cols 3, 4) and IPC (cols 6, 7); no SLL heads then
        read_pdf_years(store, f, {"3": (2012, "it_act_total"), "4": (2013, "it_act_total"),
                                  "6": (2012, "ipc_total"), "7": (2013, "ipc_total")}, "cyber_", "18.1")


# ---------------------------------------------------------------- main
def main(src, out):
    global SRC
    SRC = src
    os.makedirs(out, exist_ok=True)
    catalog = list(csv.DictReader(open(os.path.join(src, "catalog.csv"), encoding="utf8")))
    store = Store()

    # The 2015 edition's multi-year files go first so each year keeps its own report's figures.
    rec = find(catalog, 2015, r"Yearwise Cases reported under Crimes against Women during 2001-2015\(Individual State\)")
    read_women_2001_2015(store, rec)
    rec = find(catalog, 2015, r"Cases Reported Under Cyber Crimes during 2014-2015\(StateUT\)", data_year=2014)
    read_cyber_2014(store, rec)

    for year in range(2017, 2025):
        rec = find(catalog, year, r"^(3A\.1 )?Crime against Women \((IPC\+SLL\) )?\(?State/UT-wise\)", exclude=r"arrest")
        if rec:
            read_summary(store, "women", year, rec, "women")
        rec = find(catalog, year, r"^(9A\.1 )?Cyber Crimes ?\(State/UT-wise\)")
        if rec:
            read_summary(store, "cyber", year, rec, "cyber")
        rec = find(catalog, year, r"Crimes? Against Women.*Crime Head-wise & States?/UT")
        if rec:
            read_heads(store, "women", year, rec, "3A.2", WOMEN_KEYS, False, "women_")
        rec = find(catalog, year, r"Cyber Crimes ?\(Crime Head-wise & States?/UT")
        if rec:
            read_heads(store, "cyber", year, rec, "9A.2", CYBER_KEYS, True, "cyber_")
        rec = find(catalog, year, r"Cyber Crimes against Women \(State")
        if rec:
            read_heads(store, "cyber", year, rec, "9A.10", CYBER_WOMEN_KEYS, True, "cyber_")
        rec = find(catalog, year, r"Cyber Crimes against Children \(State")
        if rec:
            read_heads(store, "cyber", year, rec, "9A.11", CYBER_CHILD_KEYS, True, "cyber_")

    read_pdf_only_years(store, catalog)
    read_354_from_district_files(store, catalog)
    read_national_cyber_heads(store, os.path.join(out, "national_cyber_crimeheads_2014_2023.csv"))
    for (st, y), cell in store.panel.items():
        if y in (2012, 2013) and "cyber_cases" not in cell and \
                "cyber_it_act_total" in cell and "cyber_ipc_total" in cell:
            cell["cyber_cases"] = cell["cyber_it_act_total"] + cell["cyber_ipc_total"]
        if y != 2016 and "women_acid_attack" in cell:
            cell["women_acid_attack_incl_attempt"] = cell["women_acid_attack"] + cell.get("women_attempt_acid_attack", 0)

    # 2024 splits Sec 354 into 354/354A/354B/354C/354D (BNS 74-78); earlier years report
    # them together under 354. Add a comparable total for 2024.
    for (st, y), cell in store.panel.items():
        parts = ["women_assault_modesty_354", "women_sexual_harassment_354a", "women_disrobe_354b",
                 "women_voyeurism_354c", "women_stalking_354d"]
        if y == 2016 and "women_assault_modesty_354" in cell:
            cell["women_assault_modesty_354_incl_abcd"] = cell["women_assault_modesty_354"]
        elif y >= 2024 and all(p in cell for p in parts):
            cell["women_assault_modesty_354_incl_abcd"] = sum(cell[p] for p in parts)
        elif y < 2024 and "women_assault_modesty_354" in cell:
            cell["women_assault_modesty_354_incl_abcd"] = cell["women_assault_modesty_354"]
    # Sexual / abusive cyber crimes. NCRB counts each case once, under its principal offence,
    # so these heads do not overlap and can be added.
    #   sexual content = IT Act Sec 67 (obscene), 67A (sexually explicit), 67B (child sexual
    #                    abuse material), other Sec 67, excluding 67C (data retention by
    #                    intermediaries), plus Sec 66E (violation of privacy: capturing or
    #                    publishing private images)
    #   abusive        = cyber stalking/bullying, cyber blackmailing/threatening,
    #                    defamation/morphing, fake profile, online abetment of suicide,
    #                    and (2024) sexual intercourse by deceitful means (BNS 69)
    for (st, y), cell in store.panel.items():
        if "cyber_it67_total" in cell:
            cell["cyber_sexual_content_total"] = (cell["cyber_it67_total"] - cell.get("cyber_it67c_retention", 0)
                                                  + cell.get("cyber_it66e_violation_privacy", 0))
        abusive = [cell.get(k) for k in ("cyber_cyber_stalking_bullying", "cyber_cyber_blackmail_threat",
                                         "cyber_defamation_morphing", "cyber_fake_profile")]
        if all(v is not None for v in abusive):
            cell["cyber_abusive_total"] = (sum(abusive) + cell.get("cyber_abetment_suicide_online", 0)
                                           + cell.get("cyber_sexual_intercourse_deceit_bns69", 0))
        if "cyber_sexual_content_total" in cell and "cyber_abusive_total" in cell:
            cell["cyber_sexual_abusive_total"] = cell["cyber_sexual_content_total"] + cell["cyber_abusive_total"]
        if cell.get("cyber_cases") and "cyber_sexual_abusive_total" in cell:
            cell["cyber_sexual_abusive_share_pct"] = round(100 * cell["cyber_sexual_abusive_total"] / cell["cyber_cases"], 2)

    write_outputs(store, out)


ID = ["state", "year", "row_type"]
PANEL_COLS = [
    ("women_cases", "women_total_cases"),
    ("women_population_lakh", "female_population_lakh"),
    ("women_rate", "women_crime_rate"),
    ("women_chargesheeting_rate", "women_chargesheeting_rate"),
    ("women_total_ipc_caw", "women_ipc_total"),
    ("women_total_sll_caw", "women_sll_total"),
    ("women_rape", "rape"),
    ("women_rape_women_18plus", "rape_women_18plus"),
    ("women_rape_girls_u18", "rape_girls_under18"),
    ("women_attempt_rape", "attempt_to_rape"),
    ("women_murder_with_rape", "murder_with_rape"),
    ("women_sexual_intercourse_deceit_bns69", "sexual_intercourse_by_deceit_bns69"),
    ("women_dowry_deaths", "dowry_deaths"),
    ("women_abetment_suicide_women", "abetment_of_suicide_of_women"),
    ("women_acid_attack", "acid_attack"),
    ("women_attempt_acid_attack", "attempt_acid_attack"),
    ("women_acid_attack_incl_attempt", "acid_attack_incl_attempt"),
    ("women_cruelty_husband_relatives", "cruelty_by_husband_or_relatives"),
    ("women_kidnap_abduction_women", "kidnapping_abduction_of_women"),
    ("women_kidnap_for_marriage", "kidnapping_to_compel_marriage"),
    ("women_assault_modesty_354", "assault_outrage_modesty_354_as_reported"),
    ("women_assault_modesty_354_incl_abcd", "assault_outrage_modesty_354_incl_354a_d"),
    ("women_sexual_harassment_354a", "sexual_harassment_354a"),
    ("women_disrobe_354b", "assault_to_disrobe_354b"),
    ("women_voyeurism_354c", "voyeurism_354c"),
    ("women_stalking_354d", "stalking_354d"),
    ("women_insult_modesty_509", "insult_to_modesty_509"),
    ("women_human_trafficking_370", "human_trafficking_370"),
    ("women_procuration_minor_girls", "procuration_of_minor_girls"),
    ("women_importation_girls", "importation_of_girls"),
    ("women_selling_girls", "selling_of_girls"),
    ("women_buying_girls", "buying_of_girls"),
    ("women_dowry_prohibition_act", "dowry_prohibition_act"),
    ("women_immoral_traffic_act", "immoral_traffic_act"),
    ("women_domestic_violence_act", "domestic_violence_act"),
    ("women_indecent_representation_act", "indecent_representation_act"),
    ("women_pocso_girls", "pocso_girl_victims"),
    ("women_cyber_women_centric", "women_centric_cyber_crimes"),
    ("cyber_cases", "cyber_total_cases"),
    ("cyber_population_lakh", "population_lakh"),
    ("cyber_rate", "cyber_crime_rate"),
    ("cyber_chargesheeting_rate", "cyber_chargesheeting_rate"),
    ("cyber_it_act_total", "cyber_it_act_total"),
    ("cyber_ipc_total", "cyber_ipc_total"),
    ("cyber_sll_total", "cyber_sll_total"),
    ("cyber_fraud_total", "cyber_fraud"),
    ("cyber_cbt_fraud", "cyber_criminal_breach_of_trust_fraud"),
    ("cyber_cheating", "cyber_cheating"),
    ("cyber_forgery", "cyber_forgery"),
    ("cyber_data_theft", "cyber_data_theft"),
    ("cyber_it66_computer_related_total", "cyber_computer_related_offences_66"),
    ("cyber_it66c_identity_theft", "cyber_identity_theft_66c"),
    ("cyber_it66d_cheating_personation", "cyber_cheating_by_personation_66d"),
    ("cyber_fake_news", "cyber_fake_news"),
    ("cyber_sexual_abusive_total", "cyber_sexual_abusive_total"),
    ("cyber_women_cyber_total", "cyber_crimes_against_women"),
    ("cyber_children_cyber_total", "cyber_crimes_against_children"),
]
SEXUAL_COLS = [
    ("cyber_cases", "cyber_total_cases"),
    ("cyber_sexual_abusive_total", "sexual_abusive_total"),
    ("cyber_sexual_abusive_share_pct", "sexual_abusive_share_pct"),
    ("cyber_sexual_content_total", "sexual_content_total"),
    ("cyber_abusive_total", "abusive_total"),
    ("cyber_it67_total", "it67_all_subsections"),
    ("cyber_it67_obscene", "it67_obscene_material"),
    ("cyber_it67a_sexually_explicit", "it67a_sexually_explicit_material"),
    ("cyber_it67b_child_sexual_material", "it67b_child_sexual_abuse_material"),
    ("cyber_it67_other", "it67_other_subsections"),
    ("cyber_it67c_retention", "it67c_retention_by_intermediaries"),
    ("cyber_it66e_violation_privacy", "it66e_violation_of_privacy"),
    ("cyber_cyber_stalking_bullying", "cyber_stalking_bullying"),
    ("cyber_cyber_blackmail_threat", "cyber_blackmail_threatening"),
    ("cyber_defamation_morphing", "defamation_morphing"),
    ("cyber_fake_profile", "fake_profile"),
    ("cyber_abetment_suicide_online", "abetment_of_suicide_online"),
    ("cyber_sexual_intercourse_deceit_bns69", "sexual_intercourse_by_deceit_bns69"),
    ("cyber_women_cyber_total", "vs_women_total"),
    ("cyber_women_cyber_blackmail_threat", "vs_women_blackmail_threatening"),
    ("cyber_women_cyber_pornography_obscene", "vs_women_pornography_obscene_material"),
    ("cyber_women_cyber_stalking_bullying", "vs_women_stalking_bullying"),
    ("cyber_women_defamation_morphing", "vs_women_defamation_morphing"),
    ("cyber_women_fake_profile", "vs_women_fake_profile"),
    ("cyber_women_sexual_intercourse_deceit", "vs_women_sexual_intercourse_by_deceit"),
    ("cyber_women_other_cyber", "vs_women_other"),
    ("cyber_children_cyber_total", "vs_children_total"),
    ("cyber_children_cyber_blackmail_harassment", "vs_children_blackmail_harassment"),
    ("cyber_children_cyber_pornography_csam", "vs_children_sexual_abuse_material"),
    ("cyber_children_cyber_stalking_bullying", "vs_children_stalking_bullying"),
    ("cyber_children_fake_profile", "vs_children_fake_profile"),
    ("cyber_children_online_games_gaming_apps", "vs_children_online_games_gaming_apps"),
    ("cyber_children_other_cyber", "vs_children_other"),
    ("women_cyber_women_centric", "caw_women_centric_cyber_total"),
    ("women_cyber_women_sexually_explicit_67a_67b", "caw_sexually_explicit_67a_67b"),
]


def row_type(st):
    return {"Total (States)": "total_states", "Total (UTs)": "total_uts", "All India": "total_india"}.get(st, "state_ut")


def fmt(col, v):
    if v == "" or v is None:
        return ""
    if isinstance(v, float):
        if v == int(v) and not col.endswith(("_rate", "_lakh", "_pct")):
            return int(v)
        return round(v, 2)
    return v


def write_wide(store, path, cols):
    keys = sorted(store.panel, key=lambda k: (k[0] if row_type(k[0]) == "state_ut" else "~" + k[0], k[1]))
    src = [c for c, _ in cols]
    with open(path, "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(ID + [name for _, name in cols])
        for st, y in keys:
            if not 2012 <= y <= 2024:
                continue
            cell = store.panel[(st, y)]
            if not any(c in cell for c in src):
                continue
            w.writerow([st, y, row_type(st)] + [fmt(name, cell.get(c, "")) for c, name in cols])


def write_outputs(store, out):
    write_wide(store, os.path.join(out, "state_women_cyber_panel.csv"), PANEL_COLS)
    write_wide(store, os.path.join(out, "state_cyber_sexual_abusive.csv"), SEXUAL_COLS)
    with open(os.path.join(out, "state_crimeheads_long.csv"), "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "state", "category", "table", "crime_head", "measure",
                                          "key", "value", "source_file"])
        w.writeheader()
        w.writerows(sorted(store.long, key=lambda r: (r["year"], r["category"], r["table"], r["state"])))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
