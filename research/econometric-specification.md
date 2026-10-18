# Econometric Specification (Draft)

**Paper:** Technology shocks and recorded cyber crime against women in India
**Data:** `data/analysis/` (see `data/analysis/codebook.md`), built by `scripts/build_analysis_panels.py`
**Claim level:** associations, supported by timing and comparison groups. Not causal effects.

## 1. Questions and hypotheses

| | Question | Hypothesis |
|---|---|---|
| H1 | Does recorded cyber crime against women grow faster in States with more internet access? | Yes, relative to offline crimes against women in the same State |
| H2 | Did the generative-AI boom (2023 onwards) raise image-based cyber crime against women more in more-connected States? | Yes, for AI-susceptible heads (obscene material, morphing, blackmail) relative to offline crimes |
| H3 | Did free AI image tools on a major platform raise synthetic-media complaints? | Yes: X's synthetic-media grievances rise after Grok image tools became free, relative to X's other categories |
| — | Cheap data (Jio, 2016) | Descriptive only: no State data on access or cyber crime against women before 2017 |

## 2. Notation and estimator

- *s* = State/UT (35 units), *c* = crime category (12), *t* = year, *p* = platform, *m* = month.
- **Estimator: Poisson pseudo-maximum likelihood (PPML)** with fixed effects. It suits counts with many
  small values and zeros, and its coefficients read as proportional changes: exp(β) − 1.
- **Offset:** log female population (`female_pop_lakh`) for crimes against women, log population for
  cyber fraud, so the models explain rates.
- **Exposure:** `Access_s` is standardised (mean 0, SD 1) across States, so β is the extra proportional
  change for a State one SD more connected.
- **Standard errors:** clustered by State. With 35 clusters, also report wild cluster (score) bootstrap
  p-values and randomisation-inference p-values (Section 7).

## 3. Model 1: internet access and the growth of cyber crime against women (H1)

**Panel:** `state_category_year_panel.csv`, 2017–2024, cyber-women and offline-women categories.

```
E[Y_sct] = exp( α_sc + δ_st + λ_ct + β · Cyber_c × Access_s × (t − 2017) + ln(FemalePop_st) )
```

- `Y_sct`: cases of category *c* in State *s*, year *t*.
- `Cyber_c` = 1 for the six cyber-crime-against-women heads (`is_cyber_vaw`), 0 for the five offline heads.
- Fixed effects:
  - `α_sc`, State × category: each State's usual level of each crime.
  - `δ_st`, State × year: anything that moves all crime against women in a State in a year (police capacity,
    reporting culture, a new women's helpline, COVID).
  - `λ_ct`, category × year: national trends in each category (e.g. the 2019 portal raising all cyber reports).
- **β > 0:** cyber crime against women grows faster than offline crime against women in more-connected States.
- **Main exposure:** `access_cams2023_15plus` (all 35 units). Alternatives: `access_nss2017_5plus` (measured at
  the start of the panel, 22 States), `access_nfhs5_15to49_avg`, `access_cams2023_15to24` (youth).

**Event-study version** (shows the year-by-year pattern and any early divergence):
```
E[Y_sct] = exp( α_sc + δ_st + λ_ct + Σ_{k≠2017} β_k · Cyber_c × Access_s × 1[t = k] + ln(FemalePop_st) )
```

**Time-varying access (2022–2024 only):** replace `Access_s × (t − 2017)` with `Cyber_c × TRAI_st`
(`trai_subs_per100`). Short panel; report as a check.

## 4. Model 2: the generative-AI boom (H2)

**Panel:** same, 2017–2024. Treated = AI-susceptible cyber heads (`is_ai_susceptible`). Comparison =
offline crimes against women.

```
E[Y_sct] = exp( α_sc + δ_st + λ_ct + β · AI_c × Post_t × Exposure_s + ln(FemalePop_st) )
```

- `Post_t` = 1 for 2023–2024 (`post_ai`). Main effects of `Post_t` and `AI_c × Post_t` are absorbed by the fixed effects.
- **Exposure options:**
  1. `access_nfhs5_15to49_avg`: internet access measured before the boom (2019-21). **Preferred for the
     connectivity question**, because the AI shock cannot have caused it.
  2. `access_cams2023_15plus`: internet access measured as the boom began.
  3. `ads_nudify_to_genai_post`: nudify-tool searches relative to general AI-tool searches, 2023–2024
     (Google Ads). **Closest to the mechanism**, and unrelated to connectivity. Measured after the boom
     began (Ads data starts Nov 2022), and abuse itself may drive searches, so read it as an association.
  4. `ads_nudify_per_lakh_post`: nudify searches per lakh people. Mixes abuse-tool demand with
     connectivity (Spearman 0.82 with general AI searches); report alongside option 3.
  5. `trends_deepfake_awareness_pre`, `trends_face_swap_pre` (Trends, 2018–2022): measured before the
     boom, but noisy for small States. Robustness only.
- **β > 0:** after 2022, image-based cyber crime against women rose more in more-exposed States.

**Event study:** `Σ_{k≠2022} β_k · AI_c × Exposure_s × 1[t = k]`. Coefficients for 2017–2021 near zero
indicate no earlier divergence; report a joint test of the pre-2022 terms.

**Time-varying search intensity (2023–2024):** replace `Post_t × Exposure_s` with `ads_nudify_per_lakh_st`
in the State × year panel. Two years only; a check, not a main result.

**Within-cyber variant:** compare AI-susceptible heads with the other cyber heads (stalking, fake profile,
other) instead of offline crimes. This removes anything common to all online crime against women.

## 5. Model 3: platform grievances around AI image tools (H3)

**Panel:** `platform_month_panel.csv`, X only, Jun 2021–Feb 2025 (before X changed its reporting format).

```
E[G_cm] = exp( α_c + μ_m + β_1 · Synthetic_c × Grok2_m + β_2 · Synthetic_c × GrokFree_m
               + θ · Synthetic_c × Election_m )
```

- `G_cm`: grievances in category *c*, month *m*. `Synthetic_c` = synthetic/manipulated media category.
- `α_c`: category fixed effects. `μ_m`: month fixed effects (anything moving all of X's grievances).
- `Grok2_m` (Aug–Nov 2024), `GrokFree_m` (Dec 2024–Feb 2025); `Election_m` = major election months.
- Already estimated in `analysis/partA/`; this specification re-runs it on the analysis panel.
- **Extension:** add Facebook and Instagram sexual-content categories as an outside comparison, with
  platform × category and platform × month fixed effects.
- **Search check:** add national monthly nudify searches (`ads_national_nudify_searches`, Nov 2022 onwards)
  to show whether demand for abuse tools moved with the Grok releases.

## 6. Descriptive analysis: Jio (2016)

- National series: TRAI internet subscriptions and World Bank internet users (2004–2025), against total
  cyber crime and sexual-content cyber crime (2012–2024), with Sep 2016 marked.
- State level, 2012–2024: `cyber_total_rate` and `sexual_content_rate` against `access_nss2017_5plus`
  (not gender-specific). Present as figures, no causal claim.

## 7. Inference, placebos and robustness

**Inference**
- State-clustered standard errors (35 clusters).
- Wild cluster (score) bootstrap p-values.
- Randomisation inference: reassign exposure across States 1,000 times; report where the real β ranks.

**Placebos**
- Replace cyber crime against women with **cyber fraud** (`is_placebo`) in Models 1 and 2: a similar
  pattern would point to general online-crime growth, not gendered abuse.
- Fake shock years in Model 2 (2019, 2020).
- Model 3: placebo release dates and the other 12 X categories (as in Part A).

**Robustness**
- Drop 2020 (COVID) and 2024 (switch to the BNS criminal code).
- Drop the States with very high reported cyber crime against women (Karnataka, Telangana) and small UTs.
- Alternative exposure measures (Section 3 and 4 lists).
- OLS on log(1 + rate) instead of PPML.
- Control for reporting capacity with `cyber_chargesheet_rate` (2020–2024).

## 8. Interpretation rules

- Outcomes are **recorded** crimes. Wording: "associated with", "coincided with". A rise may reflect more
  abuse, more reporting, or both.
- The State × year fixed effects absorb any State-wide change in reporting of crimes against women; only
  reporting changes specific to cyber crime, and more so in connected States, remain as an alternative
  explanation. Say so explicitly.
- Report effects as rate ratios, e.g. "a State one SD more connected saw cyber crime against women grow
  X% faster per year than offline crime against women".

## 9. Tables and figures

| # | Content |
|---|---|
| Fig 1 | National internet use and cyber crime, 2004–2024, Jio marked |
| Table 1 | Descriptive statistics, 2017 vs 2024, by category |
| Table 2 | Model 1: access and growth of cyber crime against women (main + alternative exposures) |
| Fig 2 | Model 1 event study |
| Table 3 | Model 2: AI boom, by exposure measure and by category |
| Fig 3 | Model 2 event study |
| Table 4 | Model 3: X grievances around Grok releases |
| Table 5 | Placebos and robustness |

## 10. Open items

- Google Ads data (nudify measures) starts in Nov 2022, so there is no State nudify measure before the
  AI boom; the pre-boom search measures come from Trends and are noisy for small States.
- `pyfixest` (PPML with high-dimensional fixed effects) is not installed in this environment; install it
  with `pip install pyfixest` before running estimates.
