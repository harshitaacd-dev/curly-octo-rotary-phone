"""Cyber crime cases by motive.

Usage: python scripts/build_motives.py data/ncrb data/clean/cyber_motives.csv

State/UT x motive for 2018-2024 (Table 9A.3, Excel). All India only for 2013-2016, typed in
from the PDF tables (18.8 in 2013, 18.7 in 2014-2015, 9A.3 in 2016) because their motive
categories differ. NCRB's 2017 State-level motive table is not online (its link serves the
city table). `motive_group` puts the categories on a common footing across years.
"""
import csv, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from ncrb_tables import parse_state_table  # noqa: E402

FILES = {2018: "2018/cyber/1681982492Table9A30.xlsx", 2019: "2019/cyber/1681725747Table9A3.xlsx",
         2020: "2020/cyber/1680861996TABLE9A3.xlsx", 2021: "2021/cyber/1679661951TABLE9A3.xlsx",
         2022: "2022/cyber/1702030805TABLE9A3.xlsx", 2023: "2023/cyber/TABLE9A3.xlsx",
         2024: "2024/cyber/TABLE9A31.xlsx"}
GROUP = {
    "Fraud": "Fraud / financial gain", "Greed/Money": "Fraud / financial gain",
    "Greed / Financial Gain": "Fraud / financial gain", "Fraud / Illegal Gain": "Fraud / financial gain",
    "Illegal Gain": "Fraud / financial gain",
    "Sexual Exploitation": "Sexual exploitation",
    "Insult to Modesty of Women": "Insult to modesty of women / eve teasing",
    "Eve Teasing / Harassment": "Insult to modesty of women / eve teasing",
    "Extortion": "Extortion / blackmailing", "Extortion/Blackmailing": "Extortion / blackmailing",
    "Motives of Blackmailing": "Extortion / blackmailing",
    "Personal Revenge": "Revenge / anger", "Anger": "Revenge / anger",
    "Emotional motives like Anger etc": "Revenge / anger", "Revenge / Settling scores": "Revenge / anger",
    "Revenge": "Revenge / anger", "Emotional Motives like Anger, Revenge, etc.": "Revenge / anger",
    "Causing Disrepute": "Causing disrepute", "Cause Disrepute": "Causing disrepute",
    "Others": "Others", "Total": "Total",
}
# All India, from the PDF tables (motive as printed -> cases).
OLD = {
    2013: {"Revenge / Settling scores": 112, "Greed/Money": 821, "Extortion": 73, "Cause Disrepute": 148,
           "Prank/Satisfaction of Gaining Control": 39, "Fraud / Illegal Gain": 1240,
           "Eve Teasing / Harassment": 1116, "Others": 2144, "Total": 5693},
    2014: {"Revenge / Settling scores": 285, "Emotional Motives like Anger, Revenge, etc.": 139,
           "Greed / Financial Gain": 1736, "Extortion": 199, "Causing Disrepute": 272,
           "Prank/Satisfaction of Gaining Control": 110, "Fraud / Illegal Gain": 495,
           "Insult to Modesty of Women": 599, "Sexual Exploitation": 357, "Political Motives": 75,
           "Inciting Hate Crimes Against Community": 174, "Inciting Hate Crimes Against Country": 11,
           "Disrupt Public Services": 25, "Sale/Purchase of Illegal Drugs/Items": 27,
           "For developing own Business/Interest": 82, "For spreading Piracy": 52,
           "Serious Psychiatric Illness viz. perversion, etc.": 0, "Steal Information for Espionage": 3,
           "Motives of Blackmailing": 159, "Others": 4822, "Total": 9622},
    2015: {"Revenge / Settling scores": 304, "Emotional Motives like Anger, Revenge, etc.": 223,
           "Greed / Financial Gain": 3855, "Extortion": 295, "Causing Disrepute": 387,
           "Prank/Satisfaction of Gaining Control": 214, "Fraud / Illegal Gain": 1119,
           "Insult to Modesty of Women": 606, "Sexual Exploitation": 588, "Political Motives": 47,
           "Inciting Hate Crimes Against Community": 205, "Inciting Hate Crimes Against Country": 12,
           "Disrupt Public Services": 33, "Sale/Purchase of Illegal Drugs/Items": 14,
           "For developing own Business/Interest": 170, "For spreading Piracy": 185,
           "Serious Psychiatric Illness viz. perversion, etc.": 12, "Steal Information for Espionage": 22,
           "Motives of Blackmailing": 293, "Others": 3008, "Total": 11592},
    2016: {"Illegal Gain": 5987, "Revenge": 1056, "Insult to Modesty of Women": 686,
           "Extortion/Blackmailing": 571, "Sexual Exploitation": 569, "Causing Disrepute": 448,
           "Inciting Hate Crimes Against Community": 149, "Developing own Business/Interest": 141,
           "Prank/Satisfaction of Gaining Control": 121, "Political Motives": 40,
           "Disrupt Public Services": 33, "Piracy": 23, "Steal Information for Espionage": 18,
           "Sale/Purchase Illegal Drugs/Other Items": 14, "Serious Psychiatric Illness viz. Perversion, etc.": 9,
           "Inciting Hate Crimes Against Country": 3, "Others": 2449, "Total": 12317},
}
AGG = {"total_states": "Total (States)", "total_uts": "Total (UTs)", "total_india": "All India"}


def main(src, out):
    rows = []
    for y, d in OLD.items():
        assert sum(v for k, v in d.items() if k != "Total") == d["Total"], y
        for m, v in d.items():
            rows.append([y, "All India", "total_india", m, GROUP.get(m, "Other named motives"), v, "PDF"])
    for y, f in FILES.items():
        seen = set()
        for r in parse_state_table(os.path.join(src, f)):
            parts = r["head"].split(" > ")
            if parts[0] == "Terrorist Activities" and len(parts) > 1 and "Total" not in parts[-1]:
                continue  # sub-heads of terrorist activities
            m = "Terrorist Activities" if parts[0] == "Terrorist Activities" else parts[-1]
            st = AGG.get(r["row_type"], r["state"])
            if (st, m) in seen:
                continue
            seen.add((st, m))
            rows.append([y, st, r["row_type"] if r["row_type"] in AGG else "state_ut", m,
                         GROUP.get(m, "Other named motives"), r["value"], f])
    with open(out, "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "state", "row_type", "motive", "motive_group", "cases", "source_file"])
        w.writerows(sorted(rows, key=lambda r: (r[0], r[2] != "state_ut", r[1], r[3])))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
