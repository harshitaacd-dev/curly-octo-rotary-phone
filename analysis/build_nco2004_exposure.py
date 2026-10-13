"""Build ILO generative-AI exposure scores for NCO-2004 3-digit groups (PLFS 2017-18 to 2020-21).

NCO-2004 follows the ISCO-88 structure, so its 3-digit groups are ISCO-88 minor groups.
Chain: ISCO-88 4-digit -> ISCO-08 4-digit -> ILO WP140 Table A1 score (Gmyrek et al. 2025;
transcription from github.com/Kpmishra1998/nco2015-ai-exposure). The score of a 3-digit
group is the unweighted mean over its linked ISCO-08 occupations, as in the NCO-2015 file.

Main score (ilo_score_uw): India's own concordance. The DGE National Classification of
Occupations listing (dge.gov.in/nat, 3,447 occupations, saved as NCO_Occupations.xlsx)
gives each occupation's NCO-2015 and NCO-2004 codes. Each NCO-2004 occupation counts once,
split equally across its NCO-2015 codes; the score of an NCO-2004 3-digit group is the
weighted mean of the NCO-2015 3-digit scores (nco2015_ai_exposure_3digit.csv) it maps to.
This matters because NCO-2004 departs from ISCO-88 in places (e.g. farm labourers are 920
in NCO-2004, 921 in ISCO-88).

ISCO route (ilo_score_isco, and the fallback for groups the DGE list does not cover):
  main (ilo_score_isco)   ILO's official ISCO-08 -> ISCO-88 correspondence table
                          (wcms_306833.pdf, read with `pdftotext -layout`). Groups the ILO
                          table does not cover fall back to the alternative links.
  alt  (ilo_score_isco_alt) Ganzeboom's isco8808/isco0888 recodes, as shipped in Ben Jann's
                          Stata package iscogen (MIT licence, github.com/benjann/iscogen),
                          both directions pooled. Robustness check.

    pdftotext -layout wcms_306833.pdf ilo_corr.txt
    python3 build_nco2004_exposure.py NCO_Occupations.xlsx nco2015_ai_exposure_3digit.csv \
        ilo_corr.txt iscogen.ado ilo_wp140_tableA1.tsv
"""

import re
import sys

import numpy as np
import pandas as pd

PAIR = re.compile(r"(?<!\d)(\d{4})\s+(\d{4})(?!\d)")


def ilo_links(path):
    """(isco88, isco08) pairs from the ILO table; each row reads 'ISCO-08 code  ISCO-88 code'."""
    pairs = set()
    for line in open(path).read().splitlines():
        pairs |= {(b, a) for a, b in PAIR.findall(line)}
    return pairs


def ganzeboom_links(ado):
    lines = open(ado).read().splitlines()

    def codelist(name):
        out, on = [], False
        for line in lines:
            if line.startswith("% CODELIST-"):
                on = line.strip() == f"% CODELIST-{name}"
                continue
            if on and line.startswith("% END"):
                break
            m = re.fullmatch(r"(\d{4}) (\d{4})", line.strip()) if on else None
            if m:
                out.append(m.groups())
        return out

    return set(codelist("isco88-isco08")) | {(b, a) for a, b in codelist("isco08-isco88")}


def scores(links, ilo):
    df = pd.DataFrame(sorted(links), columns=["isco88", "isco08"]).merge(ilo, on="isco08")
    df["nco2004_3d"] = df["isco88"].str[:3]
    df = df[~df["nco2004_3d"].str.endswith("0")]  # 3-digit codes ending in 0 are aggregates
    df = df.drop_duplicates(["nco2004_3d", "isco08"])
    df["high"] = df["Exposure"].isin(["Gradient 3", "Gradient 4"])
    g = df.groupby("nco2004_3d")
    return pd.DataFrame({
        "ilo_score_uw": g["mean"].mean().round(4),
        "ilo_high_grad_share": g["high"].mean().round(4),
        "n_isco08_linked": g.size(),
        "isco08_codes": g["isco08"].apply(lambda s: " ".join(sorted(s))),
    })


def dge_scores(xlsx, nco2015_csv):
    occ = pd.read_excel(xlsx, dtype=str).dropna(subset=["NCO 2004"])
    rows = [(r["NCO 2015"], c.strip()) for _, r in occ.iterrows()
            for c in re.split(r"[;,]", r["NCO 2004"]) if re.fullmatch(r"\d{4}\.\d{2}", c.strip())]
    d = pd.DataFrame(rows, columns=["nco2015", "nco2004"])
    d["w"] = 1 / d.groupby("nco2004")["nco2004"].transform("size")
    d["g15"], d["nco2004_3d"] = d["nco2015"].str[:3], d["nco2004"].str[:3]
    exp15 = pd.read_csv(nco2015_csv, dtype={"nco2015_3d": str}).set_index("nco2015_3d")
    d["s"] = d["g15"].map(exp15["ilo_score_uw"])
    d["h"] = d["g15"].map(exp15["ilo_high_grad_share"])
    d = d.dropna(subset=["s"])
    g = d.groupby("nco2004_3d")
    return pd.DataFrame({
        "ilo_score_uw": g.apply(lambda t: np.average(t["s"], weights=t["w"])).round(4),
        "ilo_high_grad_share": g.apply(lambda t: np.average(t["h"], weights=t["w"])).round(4),
        "n_dge_occupations": g["nco2004"].nunique(),
        "nco2015_groups": g["g15"].apply(lambda s: " ".join(sorted(set(s)))),
    })


def main(xlsx, nco2015_csv, ilo_corr_txt, ado, ilo_tsv):
    ilo = pd.read_csv(ilo_tsv, sep="\t", dtype={"code4": str}).rename(columns={"code4": "isco08"})
    isco = scores(ilo_links(ilo_corr_txt), ilo)
    alt = scores(ganzeboom_links(ado), ilo)
    isco = pd.concat([isco, alt.loc[alt.index.difference(isco.index)]])
    dge = dge_scores(xlsx, nco2015_csv)
    fallback = isco.loc[isco.index.difference(dge.index), ["ilo_score_uw", "ilo_high_grad_share"]]
    out = pd.concat([dge.assign(source="DGE"), fallback.assign(source="ISCO route")])
    out["ilo_score_isco"] = isco["ilo_score_uw"].reindex(out.index)
    out["ilo_score_isco_alt"] = alt["ilo_score_uw"].reindex(out.index)
    out.index.name = "nco2004_3d"
    out.sort_index().reset_index().to_csv("nco2004_ai_exposure_3digit.csv", index=False)
    both = out.dropna(subset=["ilo_score_isco"])
    both = both[both["source"] == "DGE"]
    r = np.corrcoef(both["ilo_score_uw"], both["ilo_score_isco"])[0, 1]
    print(f"{len(out)} NCO-2004 groups: {len(dge)} from the DGE concordance, {len(fallback)} from the "
          f"ISCO route ({', '.join(fallback.index)}). DGE vs ISCO-route correlation: {r:.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
