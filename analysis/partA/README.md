# Part A: Grok image-generation releases and synthetic-media grievances on X (India)

**Data:** monthly user-grievance counts from the India IT Rules compliance reports of X, Facebook,
Instagram and Google (`data/clean/platform_grievances_monthly.csv`, built by
`scripts/platform_panel.py` from `data/external/india_it_rules_reports.xlsx`).

**Run:** `python scripts/partA_estimate.py data/clean/platform_grievances_monthly.csv analysis/partA`,
then `python scripts/partA_chart.py analysis/partA`. Full output: `results.json`,
`event_study.csv/.png`, `ri_categories.csv`, `ri_dates.csv`.

**Design:** Poisson regressions with fixed effects, X sample Jun 2021–Feb 2025. From Mar 2025 X's
synthetic-media counts drop to ~0 together with total grievances (a reporting change), and from
Sep 2025 X reports shares.
- **Treated outcome:** X's "Misinformation / Synthetic and Manipulated Media" grievances, compared
  with X's 12 other grievance categories.
- **Fixed effects:** category + month. Month effects absorb anything that moves all of X's
  grievances together.
- **Post-release periods:** P1 = Grok-2 image generation (Aug–Nov 2024); P2 = Grok + Aurora free
  for all users (Dec 2024–Feb 2025).
- **Election control:** synthetic × election months, for major state and national elections.
  The coding is approximate: the X reporting months containing the end of campaigning, polling
  and counting.

## Results (rate ratios = exp(coefficient))

| Model | Grok-2 images (P1) | Free Grok + Aurora (P2) | Notes |
|---|---|---|---|
| M1 within-X DiD | 1.71 (p = 0.16) | **21.4 (p < 0.001)** | robust SE |
| M2 + election control | 1.26 (p = 0.55) | **17.2 (p < 0.001)** | elections alone: 3.6× (p < 0.001) |
| R1 sample to Aug 2025 + regime dummy | 1.25 (p = 0.56) | **17.1 (p < 0.001)** | |
| R2 log(1+count) OLS | e^1.45 (p < 0.001) | e^3.28 (p < 0.001) | election term not significant |
| M4 placebo: Grok-1 (Nov 2023) | 0.52 (p = 0.19) | – | no effect, as expected |
| M5 randomisation inference across 13 categories | rank p = 0.15 | **rank p = 0.077** (largest of all 13; smallest p possible) | |
| M6 placebo event dates 2022–2023 | – | all 24 placebo estimates negative; real P1 and P2 exceed all | |

**Event study** (`event_study.png`): synthetic-media grievances are well below the 2021–mid-2023
reference level from Aug 2023 to Mar 2024. They rise to about 1–3× in election months and after
Grok-2's image release. They reach **5.3× in Dec 2024** (95% CI 1.8–15.8; no election that month),
the first month after Grok and Aurora became free, then about **35× in Jan and Feb 2025**.

**Cross-platform triple difference (M7):** X compared with Facebook, Instagram and Google, within
the sexual content, impersonation and harassment groups.

| Group | P1 | P2 |
|---|---|---|
| Sexual content | 0.56 (p = 0.05) | 0.67 (p = 0.28) |
| Impersonation | 0.78 (p = 0.47) | **2.97 (p = 0.02)** |
| Harassment | 0.40 (p < 0.001) | 0.42 (p = 0.01) |

## Reading
1. **The free rollout of Grok with the Aurora image generator (Dec 2024) is followed by a large
   rise in synthetic-media grievances on X.** It is robust to X's month effects, the election
   control, the estimator (Poisson or log-OLS) and the sample end. No other X category rose as
   much. X's impersonation grievances also rose relative to the other platforms.
2. **The Grok-2 image release (Aug 2024) shows at most a modest rise.** It is not significant in
   the Poisson models once elections are controlled for, but is significant in log-OLS. Fragile.
3. **No sign of extra sexual-content grievances on X** after either release, relative to the other
   platforms. Synthetic-media complaints rose without a matching rise in adult-content complaints.
4. **The text-only Grok-1 release (placebo) shows no effect.**

## Caveats
- **Election misinformation is mixed in:** until Aug 2025 X's category combined misinformation
  with synthetic media. The Jan–Feb 2025 peak overlaps the Delhi election. Election months alone
  are worth about 3.6×, far below the ~35× peak, and Dec 2024 (no election) is already 5×. But
  AI-made election content is itself plausible, so the two cannot be fully separated.
- **Weak inference:** there is only one treated category on one platform. Clustered SEs with 13
  categories are unreliable; randomisation inference is coarse (minimum p = 1/13).
- **Short window:** the post period is three months before X's reporting changes cut the series.
  This gives a short-run effect, not a persistent one.
- **What is measured:** grievances through X's formal India channel, not incidents. The channel
  missed the Jan 2026 Grok "undressing" episode entirely.
