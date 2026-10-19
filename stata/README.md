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

**`state_access.dta`** — one row per State: every access measure, TRAI per 100 for December 2021–2025, search
exposure measures.

## Do-files

Run from the repository root (the folder that contains `stata/`):

```stata
cd "/Users/Academic/Downloads/curly-octo-rotary-phone-claude-stata"   // your path
do stata/part1.do
do stata/part2.do
do stata/part3.do
```

| Do-file | Runs | Writes |
|---|---|---|
| `part1.do` | 1a Model 1 (with crime types, event study, placebo, robustness, labelling controls); 1b across States; 1c TRAI within States, Delhi + Haryana merged; 1d India by year | `part1_results.txt`, `part1_national.png` |
| `part2.do` | 2a Model 2 (all exposures, event study and pre-trend test, crime types, placebo, fake years, robustness); 2b labelling controls and stable versus unstable States | `part2_results.txt`, `part2_event_study.csv/.png` |
| `part3.do` | 3a NCRB versus platform complaints by year; 3b growth index (2022 = 100); 3c every platform's sexual-content share; 3d reporting chain 2023 to 2024 | `part3_results.txt`, `part3_*.png` |

Each do-file prints the result expected from the Python version next to each model, so you can check that
Stata reproduces it. Packages (installed automatically if missing): `ftools`, `reghdfe`, `ppmlhdfe`.
