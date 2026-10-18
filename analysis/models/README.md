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

## Reading

The panel cannot detect an AI-boom signal in police-recorded data: estimates are null under every exposure
measure, including the main specification, which passes its pre-trend test. Read together with
`analysis/funnel/` (online complaints rise 18–21× from 2023 to 2024 while NCRB counts fall), the result is
consistent with the signal being lost between online abuse and police records, not with the absence of abuse.
