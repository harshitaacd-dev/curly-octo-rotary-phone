"""Harmonise the datasets pulled by threat_text_pull.py into one long table.

Outputs (data/text_threats/):
  threat_corpus_full.csv.gz   every labelled text from every source
  threat_corpus_positives.csv rows labelled as a threat or sexual threat, or
                              matching the rape lexicon
  threat_corpus_summary.csv   counts per source

Harmonised columns:
  source, source_id, platform, language, split, text,
  threat          1/0 = source labels this text as a (violent) threat; blank = source has no threat label
  sexual_threat   1/0 = source labels this as a sexual / rape threat;  blank = no such label in source
  gendered        1/0 = source says text targets women / gender;       blank = not labelled
  threat_score    continuous threat score where the source has one (else blank)
  rape_lexicon    1 if text matches RAPE_RE (keyword heuristic, NOT a label)
  original_label  the source's own label(s), verbatim
  licence

Usage: python scripts/build_threat_corpus.py
"""
import glob
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent / "data" / "text_threats"
RAW = ROOT / "raw"

# Rape / sexual-assault vocabulary in English, Hindi (Devanagari + romanised),
# Bangla and Tamil. A keyword hit is a retrieval aid, not an annotation:
# it also fires on news, survivor accounts and counter-speech.
RAPE_RE = re.compile(
    r"\b(?:rap(?:e|ed|es|ing|ist|ists|ey)|gang\s*-?\s*rap\w*|molest\w*|sexual(?:ly)?\s+assault\w*"
    r"|balatkar\w*|dhorshon\w*|karpazh\w*)\b"
    r"|बलात्कार|रेप(?:िस्ट)?(?![\u0900-\u097F])|ধর্ষণ|ধর্ষ|கற்பழி|வன்புணர்",
    re.IGNORECASE,
)

COLS = ["source", "source_id", "platform", "language", "split", "text", "threat",
        "sexual_threat", "gendered", "threat_score", "original_label", "licence"]


def b(x):
    return x.astype("Int64") if hasattr(x, "astype") else x


def edos():
    d = pd.read_csv(RAW / "edos/edos_labelled_aggregated.csv")
    sexist = d.label_sexist.eq("sexist")
    return pd.DataFrame({
        "source": "EDOS (SemEval-2023 T10)", "source_id": d.rewire_id,
        "platform": "Reddit/Gab", "language": "en", "split": d.split, "text": d.text,
        "threat": b(d.label_category.str.startswith("1.")),
        "sexual_threat": pd.NA,
        "gendered": pd.Series(pd.NA, index=d.index, dtype="Int64").mask(sexist, 1),
        "original_label": d.label_sexist + " | " + d.label_category + " | " + d.label_vector,
        "licence": "CC0-1.0",
    })


def guest():
    d = pd.read_csv(RAW / "guest_misogyny/data/final_labels.csv")
    l3 = d.level_3.fillna("")
    return pd.DataFrame({
        "source": "Guest et al. 2021 Reddit misogyny", "source_id": d.entry_id,
        "platform": "Reddit", "language": "en", "split": d.split, "text": d.body,
        "threat": b(l3.str.startswith("Threatening")),
        "sexual_threat": b(l3.eq("Threatening_Sexual_violence")),
        "gendered": b(d.level_1.eq("Misogynistic")),
        "original_label": d[["level_1", "level_2", "level_3"]].fillna("").agg(" | ".join, axis=1),
        "licence": "CC-BY-4.0 (ACL Anthology attachment)",
    })


def comma():
    rows = []
    for f in glob.glob(str(RAW / "comma/train_test_dev/*/*/*.csv")):
        d = pd.read_csv(f, sep="\t", dtype=str)
        p = Path(f)
        d["annotator"], d["split"] = p.parts[-3], p.parts[-2]
        d["platform"] = re.sub(r"_?corpus.*|_\d+$|\.csv$", "", p.name).split("_")[0].capitalize()
        rows.append(d)
    d = pd.concat(rows, ignore_index=True)
    # One row per annotator; collapse to one row per text with majority vote.
    d["sth"] = d["Aggression Intensity"].eq("STH")
    d["pth"] = d["Aggression Intensity"].eq("PTH")
    d["gent"] = d["Gender Bias"].eq("GENT")
    d["gen"] = d["Gender Bias"].isin(["GEN", "GENT"])
    g = d.groupby("Text", sort=False)
    a = g.agg(source_id=("ID", "first"), platform=("platform", "first"), split=("split", "first"),
              n=("annotator", "nunique"), sth=("sth", "mean"), pth=("pth", "mean"),
              gent=("gent", "mean"), gen=("gen", "mean")).reset_index()
    lab = g.apply(lambda x: "; ".join(
        "/".join(map(str, r)) for r in
        x[["Aggression", "Aggression Intensity", "Gender Bias"]].fillna("").itertuples(index=False)),
        include_groups=False)
    a = a.merge(lab.rename("lab").reset_index(), on="Text")
    a = a[~a.Text.str.startswith("http")]  # header rows holding the video/post URL
    script = a.Text.str.contains(r"[ঀ-৿]").map({True: "bn"})
    script = script.fillna(a.Text.str.contains(r"[ऀ-ॿ]").map({True: "hi", False: "mixed (en/hi/bn/mni, Latin script)"}))
    sexual = (a.sth >= 0.5) | (a.gent >= 0.5)
    return pd.DataFrame({
        "source": "ComMA v0.2", "source_id": a.source_id, "platform": a.platform,
        "language": script, "split": a.split, "text": a.Text,
        "threat": b(sexual | (a.pth >= 0.5)), "sexual_threat": b(sexual),
        "gendered": b(a.gen >= 0.5),
        "threat_score": (a.sth + a.pth).clip(upper=1).round(3),
        "original_label": "n_annot=" + a.n.astype(str) + "; " + a.lab,
        "licence": "CC-BY-NC-SA-4.0",
    })


def uli():
    out = []
    for lang in ["en", "hi", "ta"]:
        for split, folder in [("train", "training"), ("test", "testing")]:
            qs = {}
            for q in (1, 2, 3):
                d = pd.read_csv(RAW / f"uli/{folder}/{split}_{lang}_l{q}.csv", engine="python")
                d = d[d.key.eq(f"question_{q}")]
                ann = d.filter(regex=f"^{lang}_a").apply(pd.to_numeric, errors="coerce")
                qs[q] = pd.DataFrame({"text": d.text, f"q{q}": ann.mean(axis=1)}).groupby("text").mean()
            m = qs[1].join(qs[2], how="outer").join(qs[3], how="outer").reset_index()
            m["lang"], m["split"] = lang, split
            out.append(m)
    m = pd.concat(out, ignore_index=True)
    m["text"] = m.text.str.strip()
    lab = m[["q1", "q2", "q3"]].round(2).astype(str)
    return pd.DataFrame({
        "source": "Uli (Tattle) oGBV", "source_id": pd.NA, "platform": "Twitter",
        "language": m.lang, "split": m.split, "text": m.text,
        "threat": pd.NA, "sexual_threat": pd.NA,
        "gendered": b((m.q1 >= 0.5) | (m.q2 >= 0.5)),
        "original_label": "mean q1_gendered_abuse_undirected=" + lab.q1
                          + "; q2_gendered_abuse_directed=" + lab.q2
                          + "; q3_explicit_aggressive=" + lab.q3,
        "licence": "CC-BY-4.0",
    })


def dynahate():
    d = pd.read_csv(RAW / "dynahate/Dynamically Generated Hate Dataset v0.2.3.csv")
    return pd.DataFrame({
        "source": "DynaHate (Vidgen et al. 2021, synthetic)", "source_id": d["acl.id"],
        "platform": "synthetic", "language": "en", "split": d.split, "text": d.text,
        "threat": b(d.type.eq("threatening")), "sexual_threat": pd.NA,
        "gendered": b(d.target.fillna("").str.contains("wom")),
        "original_label": d.label + " | " + d.type.fillna("") + " | " + d.target.fillna(""),
        "licence": "CC-BY-4.0",
    })


def hatecheck():
    d = pd.read_csv(RAW / "hatecheck/test_suite_cases.csv")
    return pd.DataFrame({
        "source": "HateCheck (synthetic tests)", "source_id": d.case_id,
        "platform": "synthetic", "language": "en", "split": "test", "text": d.test_case,
        "threat": b(d.functionality.str.startswith("threat_")), "sexual_threat": pd.NA,
        "gendered": b(d.target_ident.eq("women")),
        "original_label": d.functionality + " | " + d.label_gold + " | " + d.target_ident.fillna(""),
        "licence": "CC-BY-4.0",
    })


def cad():
    d = pd.read_csv(RAW / "cad/data/cad_v1_1.tsv", sep="\t", dtype=str)
    d = d[~d.split.str.startswith("exclude")]
    g = d.groupby("id", sort=False)
    a = g.agg(text=("meta_text", "first"), split=("split", "first"),
              sec=("annotation_Secondary", lambda s: "; ".join(s.dropna().unique())),
              tgt=("annotation_Target_top.level.category", lambda s: "; ".join(s.dropna().unique()))
              ).reset_index()
    return pd.DataFrame({
        "source": "CAD (Vidgen et al. 2021)", "source_id": a.id, "platform": "Reddit",
        "language": "en", "split": a.split, "text": a.text,
        "threat": b(a.sec.str.contains("threatening language")), "sexual_threat": pd.NA,
        "gendered": b(a.tgt.str.contains("gender")),
        "original_label": a.sec.replace("", "Neutral") + " | target: " + a.tgt,
        "licence": "CC-BY-4.0",
    })


def mhs():
    d = pd.read_parquet(RAW / "measuring_hate_speech/measuring-hate-speech.parquet",
                        columns=["comment_id", "platform", "text", "violence", "target_gender_women",
                                 "hate_speech_score"])
    a = d.groupby("comment_id").agg(text=("text", "first"), platform=("platform", "first"),
                                    v=("violence", "mean"), w=("target_gender_women", "mean"),
                                    hs=("hate_speech_score", "first")).reset_index()
    plat = {0: "Reddit", 1: "Twitter", 2: "YouTube", 3: "Gab"}
    return pd.DataFrame({
        "source": "Measuring Hate Speech (Berkeley D-Lab)", "source_id": a.comment_id,
        "platform": a.platform.map(plat).fillna(a.platform.astype(str)), "language": "en",
        "split": "train", "text": a.text,
        # 'violence' item: 0-4 agreement that the comment calls for violence
        "threat": b(a.v >= 2), "sexual_threat": pd.NA, "gendered": b(a.w >= 0.5),
        "threat_score": (a.v / 4).round(3),
        "original_label": "mean_violence_0to4=" + a.v.round(2).astype(str)
                          + "; hate_speech_score=" + a.hs.round(2).astype(str),
        "licence": "CC-BY-4.0",
    })


def ethos():
    d = pd.read_csv(RAW / "ethos/Ethos_Dataset_Multi_Label.csv", sep=";")
    return pd.DataFrame({
        "source": "ETHOS multi-label", "source_id": d.index, "platform": "YouTube/Reddit",
        "language": "en", "split": "train", "text": d.comment,
        "threat": b(d.violence >= 0.5), "sexual_threat": pd.NA, "gendered": b(d.gender >= 0.5),
        "threat_score": d.violence.round(3),
        "original_label": "violence=" + d.violence.round(2).astype(str) + "; gender=" + d.gender.round(2).astype(str),
        "licence": "GPL-3.0",
    })


def civil():
    files = sorted(glob.glob(str(RAW / "civil_comments/*.parquet")))
    if not files:
        print("  civil_comments not downloaded; skipping")
        return None
    parts = []
    for f in files:
        d = pd.read_parquet(f)
        d["split"] = Path(f).name.split("-")[0]
        d["row"] = Path(f).stem + ":" + d.index.astype(str)
        # Keep only the threat-relevant slice of 2M comments.
        parts.append(d[(d.threat >= 0.5) | d.text.str.contains(RAPE_RE)])
    d = pd.concat(parts, ignore_index=True)
    return pd.DataFrame({
        "source": "Civil Comments (Jigsaw) subset", "source_id": d.row, "platform": "Civil Comments",
        "language": "en", "split": d.split, "text": d.text,
        "threat": b(d.threat >= 0.5), "sexual_threat": pd.NA, "gendered": pd.NA,
        "threat_score": d.threat.round(3),
        "original_label": "threat=" + d.threat.round(2).astype(str) + "; sexual_explicit="
                          + d.sexual_explicit.round(2).astype(str) + "; toxicity=" + d.toxicity.round(2).astype(str),
        "licence": "CC0-1.0",
    })


def main():
    frames = []
    for fn in [edos, guest, comma, uli, dynahate, hatecheck, cad, mhs, ethos, civil]:
        print(fn.__name__)
        f = fn()
        if f is not None:
            frames.append(f.reindex(columns=COLS))
    df = pd.concat(frames, ignore_index=True)
    df = df[df.text.notna() & df.text.str.strip().ne("")]
    df["rape_lexicon"] = df.text.str.contains(RAPE_RE).astype(int)
    for c in ["threat", "sexual_threat", "gendered"]:
        df[c] = df[c].astype("Int64")
    df = df[COLS[:9] + ["threat_score", "rape_lexicon", "original_label", "licence"]]

    df.to_csv(ROOT / "threat_corpus_full.csv.gz", index=False, compression="gzip")
    pos = df[df.threat.eq(1).fillna(False) | df.sexual_threat.eq(1).fillna(False) | df.rape_lexicon.eq(1)]
    pos.to_csv(ROOT / "threat_corpus_positives.csv", index=False)

    s = df.groupby("source").agg(
        texts=("text", "size"),
        has_threat_label=("threat", lambda x: x.notna().any()),
        threat=("threat", lambda x: int(x.eq(1).sum())),
        has_sexual_threat_label=("sexual_threat", lambda x: x.notna().any()),
        sexual_threat=("sexual_threat", lambda x: int(x.eq(1).sum())),
        gendered=("gendered", lambda x: int(x.eq(1).sum())),
        gendered_threat=("threat", lambda x: int((x.eq(1) & df.loc[x.index, "gendered"].eq(1)).sum())),
        rape_lexicon=("rape_lexicon", "sum"),
        licence=("licence", "first"),
    ).reset_index()
    s.to_csv(ROOT / "threat_corpus_summary.csv", index=False)
    print(s.to_string())
    print(f"full: {len(df)} rows; positives: {len(pos)} rows")


if __name__ == "__main__":
    main()
