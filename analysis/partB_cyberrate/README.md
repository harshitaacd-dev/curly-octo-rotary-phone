# Part B, stand-in exposure (pipeline test)

`python scripts/partB_estimate.py --exposure cyberrate --out analysis/partB_cyberrate`

- **Exposure:** each state's 2017–2021 cyber crime rate per lakh population. This is a stand-in
  until Google Trends exposure is pulled. It measures how "online" a state's crime already was,
  not exposure to AI tools.
- **Model:** Poisson on State/UT × category × year (2017–2024, 35 units after merging boundary
  changes) with state×category, state×year and category×year fixed effects. Treatment =
  AI-susceptible cyber crimes against women × Post(2023–24) × exposure (standardised). Comparison
  = offline crimes against women. SEs clustered by state.

## Results
| Estimate | Value |
|---|---|
| Main effect | rate ratio 0.95 per SD of exposure (coef −0.049, SE 0.131, p = 0.71) |
| Dropping 2024 | coef 0.008, p = 0.95 |
| Pre-trends (2017–2020 vs 2021) | joint p = 0.80, no sign of diverging trends |
| Event study (2017 … 2024) | −0.08, −0.01, 0.06, −0.00, [0], −0.09, −0.02, −0.13 |

**By category** (coef, p):

| Category | Coef | p |
|---|---|---|
| Defamation/morphing | 1.65 | 0.08 |
| Blackmail | 0.14 | 0.66 |
| Obscene material | −0.08 | 0.41 |
| Stalking/bullying | −0.05 | 0.87 |
| Fake profile | −0.86 | 0.16 |

**Reading:** no differential post-2022 rise in AI-susceptible cyber crimes against women in states
with more prior cyber crime. Morphing is the only category that leans positive (weakly, p = 0.08,
small counts).
