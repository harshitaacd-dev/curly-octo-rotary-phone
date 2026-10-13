"""Build ILO generative-AI exposure scores for NCO-2004 3-digit groups (PLFS 2017-18 to 2020-21).

NCO-2004 follows the ISCO-88 structure, so its 3-digit groups are ISCO-88 minor groups.
Chain: ISCO-88 4-digit -> ISCO-08 4-digit -> ILO WP140 Table A1 score (Gmyrek et al. 2025;
transcription from github.com/Kpmishra1998/nco2015-ai-exposure). The score of a 3-digit
group is the unweighted mean over its linked ISCO-08 occupations, as in the NCO-2015 file.

Links:
  main (ilo_score_uw)     ILO's official ISCO-08 -> ISCO-88 correspondence table
                          (wcms_306833.pdf, read with `pdftotext -layout`). Groups the ILO
                          table does not cover fall back to the alternative links.
  alt  (ilo_score_uw_alt) Ganzeboom's isco8808/isco0888 recodes, as shipped in Ben Jann's
                          Stata package iscogen (MIT licence, github.com/benjann/iscogen),
                          both directions pooled. Robustness check.

    pdftotext -layout wcms_306833.pdf ilo_corr.txt
    python3 build_nco2004_exposure.py ilo_corr.txt iscogen.ado ilo_wp140_tableA1.tsv
"""

import re
import sys

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


def main(ilo_corr_txt, ado, ilo_tsv):
    ilo = pd.read_csv(ilo_tsv, sep="\t", dtype={"code4": str}).rename(columns={"code4": "isco08"})
    main_ = scores(ilo_links(ilo_corr_txt), ilo)
    alt = scores(ganzeboom_links(ado), ilo)
    missing = alt.index.difference(main_.index)
    out = pd.concat([main_.assign(link_source="ILO"), alt.loc[missing].assign(link_source="Ganzeboom")])
    out["ilo_score_uw_alt"] = alt["ilo_score_uw"].reindex(out.index)
    out.index.name = "nco2004_3d"
    out.sort_index().reset_index().to_csv("nco2004_ai_exposure_3digit.csv", index=False)
    both = out.dropna(subset=["ilo_score_uw_alt"])
    r = both["ilo_score_uw"].corr(both["ilo_score_uw_alt"])
    print(f"{len(out)} NCO-2004 groups ({len(missing)} from fallback: {', '.join(missing)}); "
          f"correlation of main and alt scores: {r:.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
