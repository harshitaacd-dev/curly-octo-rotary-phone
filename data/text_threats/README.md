# Text datasets on rape threats, sexual threats and gendered threats

This folder holds human-annotated social-media text that labels **threats**, **sexual or rape threats**, or **gendered and misogynistic abuse**. It is meant for text mining and classifier training. Every dataset here is openly licensed and was downloaded from its official source.

> **Content warning.** These files contain explicit threats of rape and violence, slurs and other abusive language.

## Rebuilding the data

```bash
python scripts/threat_text_pull.py       # downloads raw files to raw/ (~560 MB including Civil Comments)
python scripts/build_threat_corpus.py    # writes the harmonised files below
```

The Civil Comments parquet files (~400 MB) are git-ignored. Only the threat-relevant subset is committed, inside the corpus files. Use `--skip-civil` to skip that download.

## Files

| File | What it contains |
|---|---|
| `threat_corpus_full.csv.gz` | All 255,490 labelled texts from the 12 sources, in one schema |
| `threat_corpus_positives.csv` | 30,526 rows that are labelled a threat or a sexual threat, or that match either keyword list |
| `threat_corpus_hinglish.csv` | 25,537 texts detected as Romanised Hindi-English (Hinglish) — see [Hinglish](#hinglish-romanised-hindi-english) |
| `threat_corpus_summary.csv` | Counts per source |
| `raw/<dataset>/` | The original files, unchanged, with each dataset's own LICENSE and README |

### Columns

| Column | Meaning |
|---|---|
| `source`, `source_id` | Dataset name and the dataset's own ID for the text |
| `platform`, `language`, `split` | Where the text comes from, its language, and the dataset's original train/dev/test split |
| `text` | The post or comment |
| `threat` | 1 or 0 if the source labels violent threats; blank if the source has no such label |
| `sexual_threat` | 1 or 0 if the source labels **sexual or rape threats** specifically. Only ComMA and Guest et al. do. |
| `gendered` | 1 or 0 if the source labels whether the text targets women or gender |
| `threat_score` | A continuous threat or violence score (0–1), where the source provides one |
| `rape_lexicon` | 1 if the text matches the rape / sexual-assault keyword regex (`RAPE_RE` in the build script). This is a **retrieval aid, not a label**: it also matches news, survivor accounts and counter-speech. |
| `hinglish` | 1 if the text looks like Romanised Hindi / Hinglish (`is_hinglish` in the build script: no Indic script, and at least two common Hindi function words such as *hai, nahi, ko, tera*) |
| `hinglish_threat_lexicon` | 1 if the text matches Romanised sexual-threat phrases (`HINGLISH_THREAT_RE`: *balatkar, rape kar\*, izzat loot, nanga kar\*, chod/pel dunga/denge, utha lenge*). This is a **retrieval aid, not a label**. |
| `original_label` | The source's own labels, verbatim |
| `licence` | The licence of the source dataset |

## Datasets included

| Source | Texts | Threat-labelled | Sexual-threat-labelled | Threat label used | Language / platform | Licence |
|---|---:|---:|---:|---|---|---|
| **ComMA v0.2** (Kumar et al. 2022/23) | 59,118 | 2,313 | **1,065** | `Aggression Intensity` = STH (sexual threat) or PTH (physical threat); `Gender Bias` = GENT (gendered threat, "such as rape threats"). Annotator majority vote. | Hindi, Bangla, Meitei, Indian English; YouTube, Twitter, Facebook, Telegram | CC BY-NC-SA 4.0 |
| **Guest et al. 2021** expert-annotated misogyny | 6,555 | 18 | 3 | `level_3` = Threatening_Sexual_violence / _Physical_violence / _Privacy | English, Reddit | CC BY 4.0 |
| **EDOS** (SemEval-2023 Task 10) | 20,000 | 443 | – | Category 1: "threats, plans to harm and incitement" (1.1 threats of harm, 1.2 incitement) – all target women | English, Reddit and Gab | CC0 |
| **Measuring Hate Speech** (Berkeley D-Lab) | 39,565 | 6,155 | – | Mean `violence` item ≥ 2 on a 0–4 scale; `gendered` = target_gender_women | English, Reddit / Twitter / YouTube / Gab | CC BY 4.0 |
| **Civil Comments** (Jigsaw), subset | 17,411 | 4,725 | – | `threat` ≥ 0.5; subset = threat ≥ 0.5 **or** rape keyword (12,757 keyword hits) | English, news comments | CC0 |
| **CAD** Contextual Abuse Dataset | 24,290 | 50 | – | Secondary label "threatening language" | English, Reddit | CC BY 4.0 |
| **DynaHate** (Vidgen et al. 2021) | 41,144 | 606 | – | type = threatening; target contains `wom` | English, synthetic adversarial | CC BY 4.0 |
| **HateCheck** | 3,728 | 273 | – | functionality `threat_dir_h` / `threat_norm_h`; target women | English, synthetic test cases | CC BY 4.0 |
| **ETHOS** multi-label | 433 | 142 | – | `violence` ≥ 0.5; `gender` ≥ 0.5 | English, YouTube and Reddit | GPL-3.0 |
| **Uli** (Tattle) oGBV | 23,265 | no threat label | – | Gendered abuse labelled by South-Asian women and LGBTQIA+ experts; use `rape_lexicon` to find threats | Hindi, Tamil, Indian English; Twitter | CC BY 4.0 |
| **TRAC-2** Hindi (2020) | 4,981 | no threat label | – | `gendered` = Sub-task B "GEN" (misogynistic / gendered aggression); aggression level OAG/CAG/NAG | Hinglish and Hindi; YouTube | CC BY-NC-SA 4.0 |
| **TRAC-1** Hindi (Kumar et al. 2018) | 15,000 | no threat label | – | Aggression level only (OAG/CAG/NAG) | Hinglish and Hindi; Facebook | Apache-2.0 (repo) |

The **gendered-threat** counts (threat = 1 and gendered = 1) are in `threat_corpus_summary.csv`. For rape threats specifically, the strongest labelled signal is ComMA (`sexual_threat`). Next come EDOS category 1 and Guest et al.'s `Threatening_Sexual_violence`. In the other sources, threat = 1 and gendered = 1 combined with `rape_lexicon` = 1 is a good starting filter, but those rows need manual review.

## Hinglish (Romanised Hindi-English)

`threat_corpus_hinglish.csv` holds every text that `is_hinglish` flags (25,537 rows). **ComMA is the only open Hinglish dataset with a threat label**, and its `sexual_threat` tag (STH / GENT) explicitly covers rape threats. No other open Hinglish corpus labels threats; TRAC-2 labels gendered aggression, and TRAC-1 labels aggression only.

| Source | Hinglish texts | Threat | Sexual threat | Gendered | Keyword hit (either list) |
|---|---:|---:|---:|---:|---:|
| ComMA v0.2 | 11,508 | 556 | **273** | 2,737 | 115 |
| TRAC-1 Hindi | 9,026 | – | – | – | 68 |
| TRAC-2 Hindi | 3,396 | – | – | 615 | 55 |
| Uli | 1,443 | – | – | 685 | 11 |
| Others (CAD r/bakchodi, MHS, …) | 164 | 9 | – | 9 | 3 |

That gives **503 Hinglish texts** that are either labelled sexual threats or match a rape / sexual-threat keyword. A practical workflow is:

1. Train on ComMA's labelled `sexual_threat` rows, using its other Hinglish rows as negatives.
2. Score the TRAC-1, TRAC-2 and Uli Hinglish rows with that model; rows with `gendered` = 1 or a keyword hit are the best candidates for manual annotation.

The keyword list also matches insults and rhetoric (*balatkari* used as an insult, "maa chod denge" as abuse, news about *balatkar*). Hand-check every hit before treating it as a threat.

**Hinglish datasets that are not openly downloadable** (none of them labels threats):

| Dataset | Labels | Access |
|---|---|---|
| Bohra et al. 2018, Hindi-English code-mixed hate speech | Hate / normal | Tweet IDs only; text by email from the authors (github.com/deepanshu1995/HateSpeech-Hindi-English-Code-Mixed-Social-Media-Text) |
| Mathur et al. 2018, Hinglish Offensive Tweets (HOT) | Non-offensive / abusive / hate | Only the profanity list is public (github.com/pmathur5k10/Hinglish-Offensive-Text-Classification) |
| Nafis et al. 2023 (WOAH), code-mixed aggression and offence | Aggression, offence | Tweet IDs only (github.com/surrey-nlp/woah-aggression-detection) |
| HASOC 2019–2021 Hindi / code-mixed | Hate / offensive / profane | Registration on the HASOC (FIRE) site |
| HECM (Kapil and Ekbal, ICON 2024) | Hate / non-hate | On request from the authors |
| HingHate (YouTube and Reddit) | Hate / non-hate | IEEE DataPort (subscription) |
| Curated Hinglish misogyny dataset (17k comments, River Publishers) | Misogynistic / not | On request from the authors |

## Relevant datasets that cannot be downloaded automatically

These datasets are relevant, but they need a request form, a login, or rehydration of tweet IDs. You would have to request them yourself.

| Dataset | Relevant label | How to get it |
|---|---|---|
| AMI @ EVALITA 2018 / IberEval 2018 (English, Italian, Spanish tweets) | "sexual_harassment" (includes threats of violence), "dominance" | Request form linked from https://github.com/MIND-Lab/ami2018 |
| Let-Mi (Arabic Levantine tweets) | "threat of violence", "sexual harassment" | Request form linked from https://github.com/bilalghanem/let-mi |
| ArMI 2021 (Arabic misogyny) | "threat of violence" | Request from the shared-task organisers (FIRE 2021) |
| MAMI, SemEval-2022 Task 5 (memes) | "violence" | Request form from the task organisers |
| EXIST 2021–2024 (English and Spanish tweets) | "sexual-violence" category | Request from the EXIST shared-task organisers (UNED) |
| Bajer Danish misogyny | Threat sub-labels | Gated Hugging Face dataset `strombergnlp/bajer_danish_misogyny` (accept the terms) |
| #MeTooMA (Gautam et al. 2020) | Allegation, hate, sarcasm, etc. | Hugging Face `midas/metooma` – **tweet IDs only**; the text must be rehydrated via the X API |
| "Call me sexist, but…" (Samory et al. 2021) | Sexism (no threat label) | GESIS data archive (login required) |
| Jigsaw Toxic Comment Classification (Kaggle) | `threat` | Kaggle login. Civil Comments, included above, is the open successor with the same `threat` label. |

## Caveats

- **Label definitions differ by source.** "Threat" ranges from explicit threats of harm (EDOS 1.1, ComMA PTH/STH) to "calls for violence" against a group (Measuring Hate Speech, ETHOS). Check `original_label` before pooling sources.
- **Sexual-threat labels are rare.** There are about 1.1k in ComMA and 3 in Guest et al. Expect heavy class imbalance.
- **ComMA** has several annotators per text. The build takes a majority vote and keeps every annotator's tags in `original_label`. Its URL header rows (the post or video link) are dropped.
- **DynaHate and HateCheck** are synthetic: annotators wrote the texts. They are useful for testing a model, but they are not real-world prevalence data.
- **Hinglish detection is heuristic.** It misses Hinglish with few function words and can include Romanised Urdu, Punjabi or Bangla. ComMA and TRAC texts that are mostly Devanagari are excluded by design; filter on `language` for those.
- **Licences.** ComMA and TRAC-2 are non-commercial (NC) and ShareAlike (SA). ETHOS is GPL-3.0. Every source asks to be cited; citation details are in `raw/<dataset>/README` where the source ships one, otherwise in the source paper.
