# All datasets

Every processed dataset for the project, in one place. These are copies: the build scripts in
`scripts/` still read from `data/`, and raw source files (about 1,230 NCRB downloads, raw text
corpora) stay in `data/ncrb/` and `data/text_threats/raw/`. Empty cell in any file = not published
or not available, not zero.

## 1. Analysis panels (`1_analysis_panels/`)
Ready for regression; built by `scripts/build_analysis_panels.py`. Column definitions in `codebook.md`.
Google Trends and Google Ads search measures are merged in (State × year and fixed State exposure).

| File | Rows | What it is |
|---|---|---|
| `state_year_panel.csv` | 453 | 35 States/UTs × 2012–2024: cyber crime against women (total and 7 heads), offline crimes against women, cyber fraud, cyber crime against children, rates, internet access, period markers |
| `state_category_year_panel.csv` | 3,360 | 35 States/UTs × 12 crime categories × 2017–2024, flagged cyber / AI-susceptible / offline / placebo |
| `platform_month_panel.csv` | 2,365 | X, Facebook, Instagram, Google grievances by category and month, 2021–2026, with Grok event markers |
| `state_access.csv` | 35 | Internet access measures, one row per State/UT |

## 2. NCRB crime data (`2_ncrb_crime/`)
From the National Crime Records Bureau's *Crime in India*, 2012–2024.

| File | Rows | What it is |
|---|---|---|
| `state_women_cyber_panel.csv` | 505 | State × year: crimes against women by head, cyber crime totals and heads, rates, population |
| `state_cyber_sexual_abusive.csv` | 505 | State × year: sexual and abusive cyber crimes by IT Act section; cyber crimes against women and children by head |
| `cyber_motives.csv` | 5,237 | Cyber crime by motive (e.g. sexual exploitation, fraud), State level 2018–2024, national 2013–2016 |
| `national_cyber_crimeheads_2014_2023.csv` | 30 | All-India cyber crime by head, 2014–2023 (Lok Sabha answer) |
| `state_crimeheads_long.csv` | 87,058 | Every crime head, long format |
| `ncrb_women_cyber_2012_2024.xlsx` | | Formatted workbook of the State datasets |
| `statewise_crimeheads_by_year.xlsx`, `statewise_cyber_crimeheads_by_year.xlsx` | | One sheet per year |

## 3. Internet access (`3_internet_access/`)

| File | What it is |
|---|---|
| `india_internet_access_by_state_age_gender.xlsx` | NSS 2017-18 (22 States), NFHS-5 2019-21, CAMS 2022-23 (State × age × gender × rural/urban), TRAI subscriptions per 100 people (Dec 2021–Jun 2026), national TRAI 2004–2026 and World Bank 2004–2025 |

## 4. Google Trends and Google Ads search volumes (`4_google_trends/`)
Nine search concepts: deepfake apps, deepfake APK downloads, free deepfake tools, deepfake makers,
face swap, video face swap, Reface, deepfake awareness, "what is a deepfake".

| File | Rows | What it is |
|---|---|---|
| `panel_state_yearly.csv` | 2,835 | State × year × concept, 2018–2026: Trends index linked to be comparable across States, with low-precision flags |
| `panel_state_monthly.csv` | 33,390 | Same, monthly, Jan 2018–Oct 2026 |
| `panel_state_ads_monthly.csv` | 14,758 | State × month × concept, Nov 2022–Sep 2026: Google Ads search volumes (actual counts, rounded into Google's buckets) |
| `keyword_volumes.csv` | 175,686 | State (and India) × keyword × month, Nov 2022–Sep 2026: Google Ads volumes for 107 keywords, **including nudify terms** (clothoff, undress app, nudify app, deepnude, kapde utarne wala app, telegram nude bot), Grok terms, and help-seeking terms (cyber crime complaint, StopNCII) |
| `national_monthly.csv` | 954 | India × month × concept, Jan 2018–Oct 2026: Trends index and estimated searches |
| `states.csv` | 1,868 | Raw yearly State Trends indices before linking |
| `panel_linking.csv`, `scaling.csv`, `calibration.csv` | | How the panels were linked across States and concepts, and calibrated to Ads volumes |

## 5. Platform grievance reports (`5_platform_grievances/`)
Monthly compliance reports under India's IT Rules 2021; one row per published number. Details in this folder's `README.md`.

| File | Rows | Platform, period |
|---|---|---|
| `meta.csv` | 6,350 | Facebook, Instagram, Threads, May 2021–Aug 2026 |
| `pinterest.csv` | 4,600 | Jun 2024–Aug 2026 |
| `snap.csv` | 3,939 | Snapchat, Jun 2021–Sep 2026 |
| `x.csv` | 1,609 | X, May 2021–Feb 2026 |
| `google.csv` | 1,358 | Google/YouTube, Apr 2021–Aug 2026 |
| `whatsapp.csv` | 901 | May 2021–Aug 2026 |
| `sharechat.csv`, `moj.csv` | 878, 757 | Jun 2021–Oct 2022 |
| `roblox.csv` | 247 | 5 months, 2025–26 |
| `platform_grievances_monthly.csv` | 2,365 | X, Facebook, Instagram, Google grievances by category, monthly (used in the Grok analysis) |
| `india_it_rules_reports.xlsx` | | All platforms in one workbook |
| `validation.csv` | 707 | Published totals checked against category sums |

## 6. Deepfakes and online abuse (`6_deepfakes_online_abuse/`)

| File | Rows | What it is |
|---|---|---|
| `factchecks_2018_2024.csv` | 2,351 | Indian fact-checks of deepfakes and manipulated media: publisher, date, verdict, whether a woman is depicted |
| `factcheck_youtube_seeds_2018_2024.csv` | 596 | YouTube videos linked from those fact-checks |
| `reddit_fakes_communities.csv` | 61 | Reddit communities sharing "fakes": size, creation date, region |
| `youtube_*_seeds_by_group.csv`, `youtube_*_seeds_per_video.csv` | 3–565 | YouTube comment collection summaries |
| `threat_corpus_full.csv.gz` | 255,490 | Combined abusive-text datasets, labelled for threats, sexual threats, gendered threats, Hinglish |
| `threat_corpus_hinglish.csv`, `threat_corpus_positives.csv` | 25,537, 30,526 | Hinglish subset; threat-positive subset |
| `threat_corpus_summary.csv` | 12 | One row per source dataset, with licence |

Some threat-corpus sources are licensed for non-commercial use only (e.g. ComMA, CC BY-NC-SA); see the summary file.
