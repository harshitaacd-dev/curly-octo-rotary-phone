# Models 1 and 2: results

Run: `python scripts/estimate_models.py` (writes `results.json` and the event-study CSVs here).
Panel: `data/analysis/state_category_year_panel.csv`, 35 State/UT units, 2017–2024.
Estimator: Poisson PPML, fixed effects State × category, State × year, category × year; standard errors
clustered by State; randomisation-inference (RI) p-values from 300 reassignments of exposure across States.
Exposure standardised across States, so **rate ratio (RR) = proportional change per one SD more exposure**.

## Headline

**No evidence of a positive association.** Recorded cyber crime against women did not grow faster in
more-connected States (Model 1), and AI-susceptible cyber crime against women did not rise more after 2022
in more-exposed States (Model 2). Estimates are small, mostly negative and not significant. Model 2 also
fails its pre-trend test, so it cannot be read as a clean before/after comparison.

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

## Model 2: the generative-AI boom (2023–2024)

Treated: AI-susceptible heads (obscene material, morphing, blackmail); comparison: offline crimes against women.

| Exposure measure | RR after 2022 | p (clustered) | p (RI) |
|---|---|---|---|
| NFHS-5 internet access (main) | 0.94 | 0.54 | 0.52 |
| CAMS 2022-23 internet access | 0.97 | 0.75 | |
| Nudify-to-general-AI search ratio | 0.78 | 0.13 | 0.03 |
| Nudify searches per lakh | 0.84 | 0.16 | |
| Trends deepfake awareness, 2018–22 | 0.84 | 0.26 | |
| Trends face swap, 2018–22 | 0.87 | <0.001 | |

- **Within cyber** (AI-susceptible vs other cyber heads): 0.70, p = 0.08.
- **Placebo, cyber fraud:** 0.71, p = 0.30.
- **By crime type:** obscene material 1.01 (p = 0.88); blackmail 0.91 (p = 0.76); morphing 0.18 (p = 0.02, small counts).
- **Robustness:** dropping 2020, 2024, or Karnataka and Telangana: RR 0.95–0.99, p 0.63–0.94.

**Pre-trends fail.** Joint test of the pre-2022 event-study terms: p = 0.002 (NFHS-5 access) and p < 0.001
(nudify ratio). Fake shock years give positive "effects" (2020: RR 1.38, p = 0.003). With the nudify ratio,
the event-study terms fall steadily from 2017 to 2022 and stay near zero after: AI-susceptible crime was
relatively high in these States early on and has been converging since, a trend that began before the AI
boom. The negative post-2022 estimates, including the one with RI p = 0.03, continue that convergence; they
are not an effect of the boom.

**Two estimates to treat with caution:** the Trends face-swap estimate has an implausibly small standard
error (0.019) for 35 clusters; and morphing has small counts (293–505 a year nationally), so its large
negative estimate is fragile.

## Reading

The panel cannot detect an AI-boom signal in police-recorded data: estimates are null under every exposure
measure, and the comparison States were already on different paths before 2023. Read together with
`analysis/funnel/` (online complaints rise 18–21× from 2023 to 2024 while NCRB counts fall), the result is
consistent with the signal being lost between online abuse and police records, not with the absence of abuse.
