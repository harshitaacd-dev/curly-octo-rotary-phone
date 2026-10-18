# Analysis panels: codebook

Built by `python scripts/build_analysis_panels.py` from `data/clean/` (NCRB, platform reports),
`data/external/internet_access/` (access workbook) and `data/external/google_trends/` (Google Trends
panels and Google Ads keyword volumes; see `datasets/README.md`, section 4). `build_report.txt` lists
row counts and coverage.

**Units.** 35 State/UT units. Boundary changes are merged for all years: Jammu & Kashmir + Ladakh,
and Dadra & Nagar Haveli + Daman & Diu. Counts are summed; rates are recomputed from the sums.
**Empty cell = not published** (or not available) for that unit and year, never zero.

## 1. `state_year_panel.csv`: one row per State/UT × year, 2012–2024 (453 rows)

| Column | Meaning | Years | Source |
|---|---|---|---|
| `state`, `year` | Keys | | |
| `cyber_vaw_cases` | Cyber crimes against women, all heads (victim-based, Table 9A.10) | 2017–2024 | NCRB |
| `cyber_vaw_obscene_material` | Publishing/transmitting obscene or sexually explicit material | 2017–2024 | NCRB |
| `cyber_vaw_morphing` | Defamation/morphing | 2017–2024 | NCRB |
| `cyber_vaw_blackmail` | Blackmailing/threatening | 2017–2024 | NCRB |
| `cyber_vaw_stalking` | Cyber stalking/bullying | 2017–2024 | NCRB |
| `cyber_vaw_fake_profile` | Fake profile | 2017–2024 | NCRB |
| `cyber_vaw_other` | Other cyber crimes against women | 2017–2024 | NCRB |
| `cyber_vaw_deceit_bns69` | Sexual intercourse by deceit (new BNS s.69 offence) | 2024 | NCRB |
| `women_centric_cyber_crimes` | Cyber crimes counted in the crime-against-women table (3A.2); a narrower cross-check | 2017–2024 | NCRB |
| `offline_vaw_cases` | Sum of five offline crimes against women: cruelty by husband/relatives, dowry deaths, kidnapping & abduction of women, assault on modesty (s.354 incl. 354A–D), insult to modesty (s.509) | 2012–2024 | NCRB |
| `women_total_cases` | All crimes against women | 2012–2024 | NCRB |
| `cyber_total_cases` | All cyber crime | 2012–2024 | NCRB |
| `cyber_fraud` | Cyber fraud (placebo: online crime not aimed at women) | 2017–2024 | NCRB |
| `cyber_crimes_against_children` | Cyber crimes against children | 2017–2024 | NCRB |
| `sexual_content_total` | IT Act s.67, 67A, 67B and 66E, all victims | 2013–2024 (2013–15: s.67 only) | NCRB |
| `sexual_abusive_total` | Sexual content plus abusive heads (stalking, blackmail, morphing, fake profile, online abetment of suicide), all victims | 2017–2024 | NCRB |
| `cyber_motive_sexual_exploitation` | Cyber crime cases with motive "sexual exploitation" | 2018–2024 | NCRB |
| `cyber_chargesheet_rate` | % of cyber crime cases chargesheeted; merged units weighted by cases | 2020–2024 | NCRB |
| `female_pop_lakh`, `population_lakh` | Female / total population, lakh (100,000) | 2017– / 2016–2024 | NCRB |
| `cyber_vaw_rate`, `offline_vaw_rate`, `women_crime_rate` | Cases per lakh women | 2017–2024 | Built |
| `cyber_total_rate`, `cyber_fraud_rate`, `sexual_content_rate` | Cases per lakh population | 2016/2017–2024 | Built |
| `access_nss2017_5plus` | % of persons 5+ who used the internet in the last 30 days, 2017-18 (fixed per state) | 22 major states | NSS 75th round |
| `access_cams2023_15plus` | % of persons 15+ who used the internet in the last 3 months, 2022-23 (fixed) | 35 units | CAMS (NSS 79th) |
| `access_cams2023_15to24` | Same, age 15–24 | 35 units | CAMS |
| `able_cams2023_15plus` | % of persons 15+ able to use the internet, 2022-23 | 35 units | CAMS |
| `access_nfhs5_15to49_avg` | Simple average of men's and women's % ever used internet, age 15–49, 2019-21 | 35 units | NFHS-5 |
| `trai_subs_per100` | Internet subscriptions (connections, not people) per 100 people, December of the year; Dec 2021 set to missing because TRAI misallocated several States | 2022–2024 | TRAI |
| `trends_<concept>` | Google Trends index, yearly mean, linked to be comparable across States within a concept. Concepts: `deepfake_awareness`, `deepfake_explainer`, `deepfake_apps`, `deepfake_apk`, `deepfake_free`, `deepfake_makers`, `face_swap`, `face_swap_video`, `reface`. Not comparable across concepts | 2018–2024 | Google Trends |
| `trends_low_precision_n` | Number of the 9 concepts flagged low precision for that State and year (anchor State averaged under 2 points a month) | 2018–2024 | Google Trends |
| `ads_<group>_searches` | Google Ads monthly search volumes summed over the year for a keyword group (Google's rounded buckets). Groups: `nudify` (20 keywords, e.g. clothoff, undress app, nudify app, deepnude, kapde utarne wala app, telegram nude bot), `grok_sexual` (grok bikini, grok spicy mode), `help_seeking` (cyber crime complaint, deepfake complaint, how to report deepfake, StopNCII, deepfake law india), `genai` (AI image/video generators, AI photo editor, Grok) | 2023–2024 | Google Ads |
| `ads_<group>_per_lakh` | The same per lakh population | 2023–2024 | Built |
| `post_jio` | 1 from 2017 (Jio launched Sep 2016) | | Built |
| `post_portal` | 1 from 2019 (National Cyber Crime Reporting Portal, Aug 2019) | | Built |
| `covid` | 1 in 2020 | | Built |
| `post_ai` | 1 from 2023 (generative-AI image tools widely available from late 2022) | | Built |
| `bns` | 1 in 2024 (new criminal code replaces the IPC from July 2024) | | Built |

**Fixed State exposure from search data** (in both panels and `state_access.csv`):

| Column | Meaning |
|---|---|
| `trends_deepfake_awareness_pre`, `trends_face_swap_pre`, `trends_deepfake_apps_pre`, `trends_reface_pre` | Mean Trends index 2018–2022, before the generative-AI boom. Noisy for small States |
| `ads_<group>_per_lakh_post` | Mean yearly Ads searches per lakh population, 2023–2024, for `nudify`, `grok_sexual`, `help_seeking`, `genai` |
| `ads_nudify_to_genai_post` | Nudify searches ÷ general AI-tool searches, 2023–2024. Interest in abuse tools relative to AI interest generally; unrelated to connectivity (Spearman −0.02 with `ads_genai_per_lakh_post`) |

Ads data starts in Nov 2022, so there is no pre-boom nudify measure. Trends regions are averaged into merged
units (population-weighted where known); Ads volumes are summed.

Survey access measures for merged units are weighted by 2022 NCRB population. Survey definitions
differ (age range, recall period), so each survey stays in its own column.

## 2. `state_category_year_panel.csv`: one row per State/UT × crime category × year, 2017–2024 (3,360 rows)

| Column | Meaning |
|---|---|
| `state`, `year`, `category` | Keys. 12 categories: 6 cyber crimes against women, 5 offline crimes against women, 1 placebo |
| `category_group` | `cyber_women`, `offline_women` or `cyber_placebo` |
| `cases` | Cases registered |
| `female_pop_lakh`, `population_lakh` | Population offsets |
| `is_cyber_vaw` | 1 = cyber crime against women |
| `is_ai_susceptible` | 1 = image-based heads most exposed to AI image tools: obscene material, defamation/morphing, blackmail/threatening |
| `is_placebo` | 1 = cyber fraud |
| access, TRAI, Trends, period columns | As in panel 1 |

The 2024-only BNS s.69 offence is not a category here (one year only).

## 3. `platform_month_panel.csv`: one row per platform × grievance category × month (2,533 rows)

| Column | Meaning |
|---|---|
| `platform` | X, Facebook, Instagram, Google, Snapchat |
| `category`, `category_group` | Grievance category as the platform names it; group = `synthetic`, `sexual`, `harassment`, `impersonation`, `child` or `placebo` |
| `month`, `count` | Month (YYYY-MM), user grievances received in India. For Snapchat: user content & account reports, joined across three report formats (Dec 2021 onwards; Jan–Feb 2022 missing); "All other reasons" = all reports minus sexual content and harassment |
| `suspect_duplicate` | 1 = Snapchat Nov 2025, which repeats Oct 2025 exactly in every category (a duplicated report in the source); exclude from analysis |
| `derived_from_share` | 1 = count computed from a published % share |
| `is_synthetic_media`, `is_sexual_content`, `is_placebo` | Group flags |
| `grok2_images` | 1 in Aug–Nov 2024 (Grok-2 image generation for X Premium) |
| `grok_free` | 1 in Dec 2024–Feb 2025 (Grok and the Aurora image model free for all X users) |
| `post_grok_free` | 1 from Dec 2024 |
| `trends_national_<concept>` | India estimated monthly searches for each of the 9 Trends concepts, Jan 2018 onwards |
| `ads_national_<group>_searches` | India Google Ads monthly searches for the keyword groups above, Nov 2022 onwards |

X changed its reporting format from Mar 2025 (category counts fall to about zero) and reports shares from
Sep 2025; see `analysis/partA/README.md`.

## `state_access.csv`

One row per unit: every access measure above, plus TRAI per 100 for each December 2021–2025.

**Facebook and Instagram "sexual" category** is Meta's "Content showing me in nudity/partial nudity or in a sexual act":
complaints by people about intimate images of themselves, which platforms must act on within 24 hours under the IT Rules.
