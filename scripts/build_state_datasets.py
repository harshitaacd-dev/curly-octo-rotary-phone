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

AGG = {"total_states": "Total (States)", "total_uts": "Total (UTs)", "total_india": "All India"}


# ---------------------------------------------------------------- catalog helpers
def find(catalog, year, title_rx, fmt=("xlsx", "xls"), exclude=None):
    hits = [r for r in catalog if int(r["year"]) == year and r["format"] in fmt
            and r["status"] in ("ok", "exists") and re.search(title_rx, r["title"], re.I)
            and not (exclude and re.search(exclude, r["title"], re.I))]
    for r in hits:
        if title_year_ok(os.path.join(SRC, r["file"]), year):
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
    ("fraud_total", r"^(Fraud\b(?!.*>)|Fraud \(Total\)|Criminal Breach of Trust/Fraud)"),
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
    rec = find(catalog, 2015, r"Cases Reported Under Cyber Crimes during 2014-2015\(StateUT\)")
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

    # 2024 splits Sec 354 into 354/354A/354B/354C/354D (BNS 74-78); earlier years report
    # them together under 354. Add a comparable total for 2024.
    for (st, y), cell in store.panel.items():
        parts = ["women_assault_modesty_354", "women_sexual_harassment_354a", "women_disrobe_354b",
                 "women_voyeurism_354c", "women_stalking_354d"]
        if y >= 2024 and all(p in cell for p in parts):
            cell["women_assault_modesty_354_incl_abcd"] = sum(cell[p] for p in parts)
        elif y < 2024 and "women_assault_modesty_354" in cell:
            cell["women_assault_modesty_354_incl_abcd"] = cell["women_assault_modesty_354"]
    for (st, y), cell in store.panel.items():
        sexual = [cell.get(k) for k in ("cyber_it67_total",)]
        abusive = [cell.get(k) for k in ("cyber_cyber_stalking_bullying", "cyber_cyber_blackmail_threat",
                                         "cyber_defamation_morphing", "cyber_fake_profile")]
        if sexual[0] is not None:
            cell["cyber_sexual_content_total"] = sexual[0] + cell.get("cyber_it66e_violation_privacy", 0)
        if y >= 2017 and all(v is not None for v in abusive):
            cell["cyber_abusive_total"] = sum(abusive) + cell.get("cyber_sexual_intercourse_deceit_bns69", 0)
        if "cyber_sexual_content_total" in cell and "cyber_abusive_total" in cell:
            cell["cyber_sexual_abusive_total"] = cell["cyber_sexual_content_total"] + cell["cyber_abusive_total"]

    write_outputs(store, out)


ID = ["state", "year", "row_type"]
PANEL_COLS = [
    "women_cases", "women_population_lakh", "women_rate", "women_chargesheeting_rate",
    "women_total_ipc_caw", "women_total_sll_caw",
    "women_rape", "women_rape_women_18plus", "women_rape_girls_u18", "women_attempt_rape",
    "women_murder_with_rape", "women_sexual_intercourse_deceit_bns69", "women_dowry_deaths",
    "women_abetment_suicide_women", "women_acid_attack", "women_attempt_acid_attack",
    "women_cruelty_husband_relatives", "women_kidnap_abduction_women", "women_kidnap_for_marriage",
    "women_assault_modesty_354", "women_assault_modesty_354_incl_abcd", "women_sexual_harassment_354a",
    "women_disrobe_354b", "women_voyeurism_354c", "women_stalking_354d", "women_insult_modesty_509",
    "women_human_trafficking_370", "women_procuration_minor_girls", "women_importation_girls",
    "women_selling_girls", "women_buying_girls", "women_dowry_prohibition_act",
    "women_immoral_traffic_act", "women_domestic_violence_act", "women_indecent_representation_act",
    "women_pocso_girls", "women_cyber_women_centric",
    "cyber_cases", "cyber_population_lakh", "cyber_rate", "cyber_chargesheeting_rate",
    "cyber_it_act_total", "cyber_ipc_total", "cyber_sll_total", "cyber_fraud_total", "cyber_cheating",
    "cyber_forgery", "cyber_data_theft", "cyber_it66_computer_related_total", "cyber_it66c_identity_theft",
    "cyber_it66d_cheating_personation", "cyber_it67_total", "cyber_fake_news",
    "cyber_sexual_abusive_total", "cyber_women_cyber_total", "cyber_children_cyber_total",
]
SEXUAL_COLS = [
    "cyber_cases", "cyber_sexual_abusive_total", "cyber_sexual_content_total", "cyber_abusive_total",
    "cyber_it67_total", "cyber_it67_obscene", "cyber_it67a_sexually_explicit",
    "cyber_it67b_child_sexual_material", "cyber_it67_other", "cyber_it66e_violation_privacy",
    "cyber_cyber_stalking_bullying", "cyber_cyber_blackmail_threat", "cyber_defamation_morphing",
    "cyber_fake_profile", "cyber_sexual_intercourse_deceit_bns69", "cyber_abetment_suicide_online",
    "cyber_women_cyber_total", "cyber_women_cyber_blackmail_threat", "cyber_women_cyber_pornography_obscene",
    "cyber_women_cyber_stalking_bullying", "cyber_women_defamation_morphing", "cyber_women_fake_profile",
    "cyber_women_sexual_intercourse_deceit", "cyber_women_other_cyber",
    "cyber_children_cyber_total", "cyber_children_cyber_blackmail_harassment",
    "cyber_children_cyber_pornography_csam", "cyber_children_cyber_stalking_bullying",
    "cyber_children_fake_profile", "cyber_children_online_games_gaming_apps", "cyber_children_other_cyber",
    "women_cyber_women_centric", "women_cyber_women_sexually_explicit_67a_67b",
]


def row_type(st):
    return {"Total (States)": "total_states", "Total (UTs)": "total_uts", "All India": "total_india"}.get(st, "state_ut")


def write_wide(store, path, cols):
    keys = sorted(store.panel, key=lambda k: (k[1], row_type(k[0]) != "state_ut", k[0]))
    with open(path, "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(ID + [c.replace("cyber_cyber_", "cyber_") for c in cols])
        for st, y in keys:
            if not 2012 <= y <= 2024:
                continue
            cell = store.panel[(st, y)]
            if not any(c in cell for c in cols):
                continue
            w.writerow([st, y, row_type(st)] + [cell.get(c, "") for c in cols])


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
