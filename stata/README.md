# Stata datasets for Parts 1–3

Every file needed to run the three parts of the paper, as Stata .dta files (format 118, Stata 14 or later).
Rebuild with `python scripts/build_stata_folder.py`. Variable names longer than 32 characters are shortened;
each variable label holds the full original name. Empty cell = not published, never zero.

Open a file in Stata with, for example: `use "stata/state_year_panel.dta", clear`

## Which file for which part

| Part | Analysis | File |
|---|---|---|
| 1a | Model 1: access and growth of cyber crime against women (State × crime × year) | `state_category_year_panel.dta` |
| 1b | Across States: access and levels of cyber crime against women | `state_year_panel.dta` |
| 1c | Within States: TRAI connections 2022–2024, Delhi + Haryana merged | `state_year_panel.dta` |
| 1 (chart) | India: internet users and cyber crime against women, by year | `national_year.dta` |
| 2a | Model 2: the AI boom (after 2022 × pre-boom access) | `state_category_year_panel.dta` |
| 2b | Labelling controls: break States, recording regimes | `labelling_breaks.dta` + `state_category_year_panel.dta` |
| 3a, 3b | Year by year and growth: platform complaints, NCRB, news incidents | `national_year.dta` |
| 3c | Every platform's complaints by category, monthly (Facebook, Instagram, X, Snapchat, Google, ShareChat, Moj) | `platform_month_panel.dta` |
| 3d | Reporting chain, 2023 to 2024 | `funnel_2023_2024.dta` |
| 3 (extra) | News-reported incidents by State and year | `news_incidents_state_year.dta` |
| all | Every access measure, one row per State | `state_access.dta` |
| 1, 2 | Controls: income per head (RBI) and urban share, one row per State | `state_controls.dta` |
| 1, 2 | Police capacity: civil police, cyber police stations and cyber cells (BPR&D 2024), one row per State | `state_police.dta` |
| 1e | Cyber police stations and cells by State and year, 2020-2024 (BPR&D) | `state_police_year.dta` |

## Files

**`state_category_year_panel.dta`** — 35 States × 12 crime categories × 2017–2024 (3,360 rows). `cases`,
`category`, `category_group` (`cyber_women`, `offline_women`, `cyber_placebo`), access and exposure measures.
Full codebook: `data/analysis/codebook.md`, section 2.

**`state_year_panel.dta`** — 35 States × 2012–2024 (453 rows). NCRB counts (`cyber_vaw_cases`,
`offline_vaw_cases`, `cyber_total_cases`, `cyber_fraud`, the six cyber heads), population (`female_pop_lakh`,
`population_lakh`), access (`access_cams2023_15plus`, `access_nss2017_5plus`, `access_nfhs5_15to49_avg`),
`trai_subs_per100` (2022–2024). Codebook section 1.

For Part 1c, merge Delhi and Haryana before estimating (TRAI's Delhi licence area includes Gurgaon and
Faridabad; see `analysis/models/README.md`):

```stata
use "stata/state_year_panel.dta", clear
keep if inrange(year, 2022, 2024) & !missing(trai_subs_per100, cyber_vaw_cases)
generate double subs_mn = trai_subs_per100 * population_lakh / 1000
replace state = "Delhi+Haryana" if inlist(state, "Delhi", "Haryana")
collapse (sum) cyber_vaw_cases offline_vaw_cases cyber_total_cases female_pop_lakh population_lakh subs_mn, by(state year)
generate double trai_10 = subs_mn * 1000 / population_lakh / 10
ppmlhdfe cyber_vaw_cases trai_10, absorb(state year) exposure(female_pop_lakh) vce(cluster state)
```

**`labelling_breaks.dta`** — 35 States × 2017–2024 (280 rows). `it_share` (IT Act share of cyber cases),
`other_share` ("other" share of cyber crimes against women), `label_break` (1 = jump of more than 30 points in
either, years with at least 20 cases), `regime` (number of breaks so far; for State × category × regime fixed
effects). 17 States have at least one break. Merge on `state year`.

**`national_year.dta`** — India, one row per year 2012–2026.
- NCRB: `cyber_vaw_cases` and its six heads, `offline_vaw_cases`, `women_total_cases`, `cyber_total_cases`,
  `cyber_fraud` (2017–2024 for cyber heads).
- Internet: `internet_users_pct`, `internet_users_mn` (World Bank/ITU).
- Platform complaints under the IT Rules, summed over the year: `<p>_all`, `<p>_sexual`, `x_synthetic`, and
  `<p>_months` (months reported; partial years are not comparable). `<p>` = `fb`, `ig`, `meta` (Facebook +
  Instagram), `x`, `snap`, `google`, `sharechat`, `moj` (ShareChat and Moj: June 2021 – October 2022 only;
  their public reports stop there).
- `meta_sexual_share_pct`: Meta intimate-image complaints as % of all complaints to Meta. Use this rather than
  raw Meta counts: all complaints to Meta rose about 7× in 2023 as the complaint route itself grew.
- News incidents (2018–2024): `news_ai_deepfake`, `news_morphed`, `news_real_or_unspecified`, `news_all_incidents`.

Cautions: 2021 covers June–December only; X changed its report format in March 2025 (category counts fall to
about zero); 2026 is partial.

**`funnel_2023_2024.dta`** — one row per stage of the reporting chain: `y2023`, `y2024`,
`ratio_2024_to_2023`, `kind` (online / recorded / missing).

**`platform_month_panel.dta`** — platform × grievance category × month (2,663 rows). `count`, `category_group`,
national search series. Drop `suspect_duplicate == 1`
(Snapchat November 2025). Codebook section 3.

**`news_incidents_state_year.dta`** — news-reported incidents by State and year, 2018–2024, by type
(AI/deepfake, morphed, real or unspecified), with police action and private-individual counts.

**`state_controls.dta`** — one row per State: `nsdp_pc_2019`, `nsdp_pc_avg` (per capita net state domestic
product, constant prices, RBI Handbook of Statistics on Indian States 2024-25, Table 20), `urban_share_cams` (urban share
of persons 15+, implied by CAMS 2022-23). Income missing for Lakshadweep and DNH-DD.

**`state_access.dta`** — one row per State: every access measure, TRAI per 100 for December 2021–2025, search
exposure measures.

## Do-files

Run from the repository root (the folder that contains `stata/`):

```stata
cd "path/to/curly-octo-rotary-phone"
do stata/run_all.do
```

| Do-file | What it runs (sections follow the Methodology in the supervisor draft) | Writes |
|---|---|---|
| `setup.do` | Finds the repository root, installs `ftools`, `reghdfe`, `ppmlhdfe`, defines helper programs; run by each part | |
| `part1.do` | Step 1 across States (no controls; + income, urban share, police capacity); Step 2 Model 1 and its checks; Step 3 TRAI connections with Delhi + Haryana combined; India by year | `part1_results.txt`, `part1_national.png` |
| `part2.do` | A the "other" category; B Model 2 for each exposure; C validity (event study, fake start years, placebo, dropping years/States); D each crime type; E labelling controls; F capacity controls; G expanding cyber policing 2020-2024 | `part2_results.txt`, `part2_event_study.csv/.png` |
| `part3.do` | A by year and each platform's sexual-content share; B main share-adjusted model with z-tests against police; C raw growth and pooled summary | `part3_results.txt`, `part3_yearly.png` |
| `run_all.do` | All three parts | |

Every model is followed by a comment with the Python result, so Stata output can be checked line by line.

**Tables and figures for the results section** are saved in `stata/tables/` (no screenshots needed): regression
tables as Word (`.rtf`) and `.csv` (rate ratios with p-values in parentheses), descriptive tables as `.csv`, the
Part 3 results table also as `.xlsx`, and charts as `.png`. Needs `estout` (installed automatically).

| File | Results section |
|---|---|
| `part1_table1_cyber_vaw_cases`, `part1_table1_offline_vaw_cases` | Part 1, Step 1: across States, no controls and with controls |
| `part1_table2_model1`, `part1_table2b_model1_types`, `part1_table2c_model1_checks` | Part 1, Model 1 and checks |
| `part1_table3_trai` | Part 1, Step 3: TRAI connections |
| `part1_table4_national.csv`, `part1_figure1_national.png` | India by year |
| `part2_table1_other_category.csv`, `part2_figure1_other_category.png` | Part 2, the "other" category |
| `part2_table2_model2` | Model 2 for each exposure |
| `part2_table3_event_study`, `part2_figure2_event_study.png` | Event study and pre-trend test |
| `part2_table4_validity` | Fake start years, placebo, dropping years/States |
| `part2_table5_types` | Each cyber crime type |
| `part2_table6_labelling` | Labelling controls |
| `part2_table7_capacity` | Capacity controls |
| `part2_table8_cyber_policing` | Expanding cyber policing, 2020-2024 |
| `part3_table1_by_year.csv`, `part3_figure1_by_year.png` | Police records and platform complaints by year |
| `part3_table2_sexual_share.csv` | Each platform's sexual-content share |
| `part3_table3_model.csv/.xlsx` | Part 3 model: share-adjusted (main) and raw growth |
