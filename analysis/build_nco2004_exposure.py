"""Build ILO generative-AI exposure scores for NCO-2004 3-digit groups (PLFS 2017-18 to 2020-21).

NCO-2004 follows the ISCO-88 structure, so its 3-digit groups are ISCO-88 minor groups.
Chain: ISCO-88 4-digit <-> ISCO-08 4-digit (Ganzeboom's isco8808/isco0888 recodes, as
shipped in Ben Jann's Stata package iscogen, MIT licence: github.com/benjann/iscogen),
then ILO WP140 Table A1 scores on ISCO-08 4-digit (Gmyrek et al. 2025; transcription
from github.com/Kpmishra1998/nco2015-ai-exposure).

Links from both recode directions are pooled, so an ISCO-88 group is linked to every
ISCO-08 occupation either recode connects it to. The score of a 3-digit group is the
unweighted mean over its linked ISCO-08 occupations, matching the NCO-2015 file.

    python3 build_nco2004_exposure.py path/to/iscogen.ado path/to/ilo_wp140_tableA1.tsv
"""

import re
import sys

import pandas as pd


def codelist(lines, name):
    pairs, on = [], False
    for line in lines:
        if line.startswith("% CODELIST-"):
            on = line.strip() == f"% CODELIST-{name}"
            continue
        if on and line.startswith("% END"):
            break
        m = re.fullmatch(r"(\d{4}) (\d{4})", line.strip()) if on else None
        if m:
            pairs.append(m.groups())
    return pairs


def main(ado, ilo_tsv):
    lines = open(ado).read().splitlines()
    links = set(codelist(lines, "isco88-isco08")) | {(b, a) for a, b in codelist(lines, "isco08-isco88")}
    ilo = pd.read_csv(ilo_tsv, sep="\t", dtype={"code4": str}).rename(columns={"code4": "isco08"})
    df = pd.DataFrame(sorted(links), columns=["isco88", "isco08"]).merge(ilo, on="isco08")
    df["nco2004_3d"] = df["isco88"].str[:3]
    df = df[~df["nco2004_3d"].str.endswith("0")]  # 3-digit codes ending in 0 are aggregates
    df = df.drop_duplicates(["nco2004_3d", "isco08"])
    df["high"] = df["Exposure"].isin(["Gradient 3", "Gradient 4"])
    g = df.groupby("nco2004_3d")
    out = pd.DataFrame({
        "ilo_score_uw": g["mean"].mean().round(4),
        "ilo_high_grad_share": g["high"].mean().round(4),
        "n_isco08_linked": g.size(),
        "isco08_codes": g["isco08"].apply(lambda s: " ".join(sorted(s))),
    }).reset_index()
    out.to_csv("nco2004_ai_exposure_3digit.csv", index=False)
    print(f"{len(out)} NCO-2004 groups written to nco2004_ai_exposure_3digit.csv")


if __name__ == "__main__":
    main(*sys.argv[1:3])
