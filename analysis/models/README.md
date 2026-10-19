# Models 1 and 2: results

Run: `python scripts/estimate_models.py` (writes `results.json` and the event-study CSVs here).
Panel: `data/analysis/state_category_year_panel.csv`, 35 State/UT units, 2017–2024.
Estimator: Poisson PPML, fixed effects State × category, State × year, category × year; standard errors
clustered by State; randomisation-inference (RI) p-values from 300 reassignments of exposure across States.
Exposure standardised across States, so **rate ratio (RR) = proportional change per one SD more exposure**.

## Headline

**No evidence of a positive association.** Recorded cyber crime against women did not grow faster in
more-connected States (Model 1), and did not rise more after 2022 in more-exposed States (Model 2). With
pre-boom internet access as the exposure, Model 2 passes its pre-trend test, so this null comes from a valid
before/after comparison.

## Model 1: internet access and growth of cyber crime against women

Outcome: all cyber crimes against women summed into one category; comparison: five offline crimes against
women. Coefficient = extra yearly growth per SD of access.

| Access measure | RR per year | p (clustered) | p (RI) | States |
|---|---|---|---|---|
| CAMS 2022-23, 15+ (main) | 0.97 | 0.38 | 0.28 | 35 |
| NSS 2017-18, 5+ | 0.98 | 0.54 | | 22 |
| NFHS-5, 15–49 | 1.02 | 0.59 | | 35 |
| CAMS 2022-23, 15–24 | 0.97 | 0.35 | | 35 |

- **By crime type** (main access measure): all six types between 0.89 and 1.01 per year, none significant.
- **Placebo, cyber fraud:** 1.06, p = 0.61.
- **Robustness:** dropping 2020, dropping 2024, or dropping Karnataka and Telangana leaves RR 0.96–0.97, p 0.30–0.43.
- **Event study** (`model1_event_study.csv`, base 2017): all coefficients small, negative and insignificant
  (−0.05 to −0.31).

## Part 1 checks: is more access associated with more recorded cyber crime against women?

Run: `python scripts/access_checks.py` (writes `access_checks.json`). Three simpler comparisons alongside Model 1.

**A. National trend, 2017–2024.** Internet users (World Bank) and cyber crime against women rise together:
elasticity 0.99, correlation of logs 0.97 (offline crimes against women: 0.09). Descriptive only: in years when
internet use grew faster, cyber crime against women did not clearly grow faster (correlation of growth rates 0.28).

**B. Across States (levels).** Poisson, year fixed effects, population offset, SE clustered by State; RR per SD of access.

| Access measure | Cyber crime against women | Offline crimes against women | All cyber crime | Cyber fraud |
|---|---|---|---|---|
| CAMS 2022-23, 15+ (35 States) | **1.54 (p = 0.010)** | 1.05 (0.77) | 1.34 (0.12) | 1.51 (0.22) |
| NSS 2017-18, 5+ (22 States) | 1.34 (0.064) | 1.07 (0.59) | 1.18 (0.30) | 1.32 (0.29) |
| NFHS-5, 15–49 (35 States) | 1.12 (0.54) | 0.97 (0.89) | 0.93 (0.76) | 0.45 (0.004) |

Better-connected States record more cyber crime against women and not more offline crime (CAMS; borderline with
NSS; not with NFHS-5). A cross-sectional correlation: such States are also richer, more urban and have more cyber
police capacity.

**C. Within States over time: TRAI connections, 2022–2024.** Poisson, State and year fixed effects, population
offset; RR per 10 more connections per 100 people. Dec 2021 excluded (TRAI misallocation).

*Delhi and Haryana are merged into one unit.* TRAI's Delhi licence area also covers Gurgaon and Faridabad
(Haryana) and Noida and Ghaziabad (UP): "Delhi Service area, apart from the State of Delhi, includes wireless
subscribers of the areas served by the local exchanges of Ghaziabad & Noida (in UP) and Gurgaon & Faridabad (in
Haryana)" (TRAI, Performance Indicator Reports). TRAI's State-wise internet count for Delhi fell from 45.1 million
(March 2023) to 37.2 million (December 2025) while the Delhi licence area grew from 52.7 to 59.9 million and
Haryana's State count rose from 22.3 to 31.9 million: a reallocation of subscriptions, not a loss of access.
Following Kumar and Somanathan (2009), the two are combined into one unit with consistent coverage, as the panel
already does for Jammu & Kashmir + Ladakh and Dadra & Nagar Haveli + Daman & Diu. Merging UP as well is a robustness
check (UP is large and the offsetting gain appears in Haryana).

| Version | RR | p | Units |
|---|---|---|---|
| **Delhi + Haryana merged (main)** | **1.30** | **0.034** | 34 |
| As reported, unmerged | 1.16 | 0.001 | 35 |
| Drop Delhi | 1.11 | 0.50 | 34 |
| Delhi + Haryana + UP merged | 1.29 | 0.22 | 33 |
| Placebo: offline crimes against women (merged) | 1.13 | 0.030 | 34 |
| Control for growth in other cyber crime (merged) | 1.18 | 0.14 | 34 |
| Cyber versus offline crimes against women in one model (merged) | 1.05 | 0.73 | 34 |

Connections and recorded cyber crime against women move together within States, but offline crimes move with
them too and the link is gone once recording capacity (other cyber crime) is controlled for: consistent with
broader growth in recording rather than an effect of access.

Sources: TRAI, *Yearly Performance Indicators 2022-23* (March 2024),
https://www.trai.gov.in/sites/default/files/2024-09/PIR_12032024_0.pdf; TRAI, *Performance Indicators Oct–Dec 2025*
(March 2026), https://trai.gov.in/sites/default/files/2026-03/QPIR_03032026_0.pdf; Kumar, H. and Somanathan, R.
(2009), "Mapping Indian Districts Across Census Years, 1971–2001", CDE Working Paper 176, Delhi School of Economics,
https://ideas.repec.org/p/cde/cdewps/176.html.

## Controls: income and urbanisation

Run: `python scripts/build_controls.py` then `python scripts/controls_checks.py` (writes `controls_checks.json`).
Controls (`data/analysis/state_controls.csv`): log per capita net state domestic product, constant prices, mean
2017-18 to 2022-23 (RBI, *Handbook of Statistics on Indian States 2024-25*, Table 20); urban share of persons 15+,
implied by CAMS 2022-23 rural, urban and total internet-use rates (Census 2011 tables could not be downloaded; the
implied shares are close to Census 2011 for the States checked). 33 States (no RBI income for Lakshadweep and
DNH-DD). Access is correlated with income (0.58) and urban share (0.61).

| Specification | Access (RR per SD) | p | Income | p | Urban share | p |
|---|---|---|---|---|---|---|
| 1b levels, cyber crime against women, no controls | 1.56 | 0.010 | | | | |
| + income | 0.64 | 0.26 | 2.55 | 0.021 | | |
| + urban share | 1.57 | 0.025 | | | 0.99 | 0.97 |
| + income and urban share | 0.84 | 0.63 | 3.45 | 0.004 | 0.44 | 0.034 |
| 1b levels, offline crimes against women, both controls | 0.92 | 0.81 | 1.11 | 0.63 | 1.02 | 0.97 |
| Model 1, both controls (per year) | 0.95 | 0.54 | 0.99 | 0.79 | 1.04 | 0.60 |
| Model 2, both controls (after 2022) | 1.23 | 0.25 | 0.93 | 0.71 | 0.86 | 0.52 |

**The cross-State link between access and recorded cyber crime against women is explained by income.** Richer
States record more cyber crime against women (and not more offline crime); once income is held fixed, access adds
nothing. Urban share alone does not change the result. Models 1 and 2 stay null with either control.

## Controls: police capacity

Run: `python scripts/police_capacity.py` (writes `data/analysis/state_police.csv`). Source: BPR&D, *Data on Police
Organizations 2024* (as on 1 January 2024): actual civil police strength (Table 2.1.3), cyber crime police stations
(Table 5.1.4, 459 nationally) and cyber cells (Appendix 8; State rows sum to 658, the report's total says 624).
`cyber_units_per_crore` = (stations + cells) per crore people; `civil_police_per_lakh_2020` = civil police per lakh
in 2020 from the India Justice Report raw data (BPR&D figures). Regressions use log of each, standardised; 33-34 States.

| Specification | Access | Income | Cyber units | Civil police | Notes |
|---|---|---|---|---|---|
| 1b levels, cyber crime against women: access, income, cyber units, police | 0.89 (p = 0.76) | 2.23 (p < 0.001) | 0.67 (p = 0.027) | 0.84 (p = 0.70) | |
| 1b levels, offline crimes, same controls | 0.96 (0.92) | 1.13 (0.58) | 1.04 (0.74) | 0.90 (0.77) | |
| Model 1, access + cyber units + police (per year) | 0.99 (0.79) | | 1.01 (0.55) | 0.96 (0.51) | null |
| Model 2, access + police 2020 (after 2022) | **1.42 (p = 0.041)** | | | 0.57 (p = 0.011) | exploratory |
| Model 2, access + police 2024 | 1.34 (0.16) | | | 0.65 (0.029) | |
| Model 2, all controls | 1.42 (0.042) | 0.95 (0.79) | 1.02 (0.81) | 0.58 (0.035) | |

- **Cyber police units do not explain recorded cyber crime against women.** Holding income fixed, States with more
  cyber stations and cells per person record *less* (0.67), probably because small north-eastern States have many
  units relative to population but few cases; the units are counted in 2024, after the outcome period.
- **Model 2 with police strength:** once civil police per lakh is held fixed, more-connected States show a larger
  post-2022 rise (1.42, p = 0.041), and better-policed States a smaller one (0.57). Access and police strength are
  correlated (0.56), so neither shows alone (1.08 and 0.78). The joint pre-trend test passes (p = 0.45), but the
  access event-study coefficients rise steadily from 2017 (-0.36, -0.23, -0.04, -0.02, 0.05; 2023: 0.26, 2024: 0.34),
  more like a continuing trend than a break, and the 2024 police measure weakens it (p = 0.16). Report as exploratory.

**Within States over time (2020–2024).** Cyber police stations and cells by State and year from the BPR&D reports for
1 January 2020, 2021, 2022 and 2024 (`data/analysis/state_police_year.csv`; 2023 = average of 2022 and 2024). National
totals match the reports (stations 169, 202, 262, 459; cells 376, 541 incl. Uttar Pradesh's footnoted 75, 548, 658).
Poisson, State and year fixed effects, population offset; RR per one-unit change in log(1 + cyber units per crore):

| Outcome | RR | p | States |
|---|---|---|---|
| Cyber crime against women | 0.83 | 0.068 | 35 |
| Offline crimes against women | 0.83 | 0.13 | 35 |
| All cyber crime | 0.90 | 0.51 | 35 |
| **Cyber fraud** | **1.63** | **0.027** | 26 |
| Cyber vs offline crimes against women, one model | 1.00 | 0.91 | 35 |

When a State adds cyber police units, it records more **cyber fraud** but not more cyber crime against women
(dropping the interpolated 2023 or Karnataka, whose count falls from 52 to 3 as it reclassified its stations, leaves
it null). Model 2 restricted to 2020–2024 with time-varying cyber units as a control: access 1.05 (p = 0.80), units
1.02 (p = 0.44). Expanding cyber policing has gone with financial-fraud recording, not with recording of cyber crime
against women.

## Model 2: the generative-AI boom (2023–2024)

Treated: all cyber crimes against women, summed into one category (as in Model 1); comparison: offline crimes
against women. Coefficient = extra change after 2022 per SD of exposure.

| Exposure measure | RR after 2022 | p (clustered) | p (RI) | Pre-trend test p |
|---|---|---|---|---|
| NFHS-5 internet access, 2019-21 (main) | 1.07 | 0.72 | 0.58 | 0.74 (passes) |
| CAMS 2022-23 internet access | 0.86 | 0.35 | | |
| Nudify-to-general-AI search ratio | 0.99 | 0.98 | 0.96 | <0.001 (fails) |
| Nudify searches per lakh | 1.00 | 0.98 | | |
| Trends deepfake awareness, 2018–22 | 1.13 | 0.57 | | |
| Trends face swap, 2018–22 | 0.74 | <0.001 | | |

- **Event study** (main exposure, base 2022): all years 2017–2024 between −0.08 and +0.06, none significant;
  joint pre-trend test p = 0.74.
- **Fake shock years** (2019, 2020, 2021, using 2017–2022 only): RR 1.06–1.10, all p > 0.16.
- **Placebo, cyber fraud:** 0.71, p = 0.30.
- **By crime type** (each head vs offline crimes): obscene material 1.02 (p = 0.88); blackmail 0.91 (p = 0.76);
  stalking 0.71 (p = 0.17); fake profile 0.49 (p = 0.41); other 1.22 (p = 0.46); morphing 0.18 (p = 0.02, small counts).
- **Robustness:** dropping 2020, 2024, or Karnataka and Telangana: RR 1.05–1.08, p 0.73–0.76.

**Cautions:** the nudify-ratio version fails its pre-trend test, so read only its main estimate (null) and not
its event study; the Trends face-swap estimate has an implausibly small standard error (0.026) for 35 clusters;
morphing has small counts (293–505 a year nationally), so its large negative estimate is fragile.

*An earlier version treated only the AI-susceptible heads (obscene material, morphing, blackmail); it was also
null but failed its pre-trend test (p = 0.002).*

## Controlling for NCRB labelling changes

A labelling break = a State-year where the IT Act share of cyber cases, or the "other" share of cyber crimes
against women, jumps by more than 30 points (years with at least 20 cases). **17 of 35 States have at least
one break.** Three controls, on each model's main specification:

| Control | Model 1 RR (p) | Model 2 RR (p) |
|---|---|---|
| None (main) | 0.97 (0.38) | 1.07 (0.72) |
| Drop the 17 States with breaks (18 left) | 0.94 (0.22) | **1.43 (0.035)** |
| State × category × recording-regime fixed effects | 0.95 (0.25) | 1.11 (0.61) |
| Control for the "other" share | 0.96 (0.29) | 1.04 (0.85) |
| Regime fixed effects + "other" and IT Act shares | 0.94 (0.13) | 1.02 (0.92) |

**The one significant result (Model 2, 18 States without breaks) is suggestive, not established.**
- For it: randomisation-inference p = 0.017; leaving out any one State keeps RR between 1.22 and 1.57
  (only dropping Kerala pushes p above 0.10); the event study rises after the boom (2021: +0.10, 2023: +0.27,
  2024: +0.49, p = 0.002) with pre-2021 terms near zero (−0.07 to +0.01).
- Against it: the joint pre-trend test rejects (p < 0.001, though Wald tests over-reject with 18 clusters);
  other exposure measures in the same 18 States are not significant (CAMS access 0.83, p = 0.37; nudify ratio
  1.36, p = 0.37); and the sample was chosen after seeing the data, one of four labelling controls.
- How to report it: as an exploratory finding: where NCRB recording is stable, there is some sign that
  better-connected States saw cyber crime against women rise more after 2022, which fits the argument that
  recording practice hides the signal elsewhere.

**All 35 States, effect allowed to differ by recording stability** (one model; stable States also get their
own post-2022 shift):

| Exposure | Stable States (18) | States with breaks (17) | Difference p |
|---|---|---|---|
| NFHS-5 access (main) | 1.54 (p = 0.031) | 0.85 (p = 0.47) | 0.048 |
| CAMS 2022-23 access | 0.82 (p = 0.34) | 0.90 (p = 0.59) | 0.73 |

The split appears with the main exposure, only just significant, and not with the alternative one.

## Reading

The panel cannot detect an AI-boom signal in police-recorded data: estimates are null under every exposure
measure, including the main specification, which passes its pre-trend test. Read together with
`analysis/funnel/` (online complaints rise 18–21× from 2023 to 2024 while NCRB counts fall), the result is
consistent with the signal being lost between online abuse and police records, not with the absence of abuse.

## Part 3: police records versus complaints to platforms

Run: `python scripts/part3_models.py` (writes `part3_results.json`). Yearly growth, 2022–2024: NCRB cyber crime against
women from the State panel (Poisson, State effects, SE clustered by State); each platform's sexual-content complaints
from its monthly reports (Poisson, month-of-year effects, HAC SE); z-test of the difference.

| Source | Growth per year | 95% range | Differs from NCRB, p | Relative to own other complaints |
|---|---|---|---|---|
| NCRB cyber crime against women | 1.13 | 1.02–1.24 | | |
| Facebook | 3.74 | 2.44–5.72 | <0.001 | 1.27 (p = 0.17) |
| X | 11.62 | 4.82–28.00 | <0.001 | 1.49 (p = 0.27) |
| Instagram | 1.62 | 0.78–3.34 | 0.34 | 1.09 (p = 0.72) |
| Snapchat | 1.18 | 1.10–1.26 | 0.49 | 0.84 (p = 0.004) |
| Google | 0.80 | 0.62–1.03 | 0.013 | 0.97 (p = 0.85) |
| Five platforms pooled (5 clusters; summary) | 2.96 | | 0.040 | |
