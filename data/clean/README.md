# Cleaned NCRB State/UT datasets, 2012–2024

Built from the NCRB *Crime in India* tables in `data/ncrb/` with
`python scripts/build_state_datasets.py data/ncrb data/clean`.

All values are **cases registered** (FIRs) unless the column says otherwise.
Each file has one row per State/UT per year, plus three aggregate rows per
year: `Total (States)`, `Total (UTs)` and `All India` (`row_type` tells them
apart). For every column and year, the State/UT rows add up to `All India`;
the build checks this.

| File | What it is |
|---|---|
| `state_women_cyber_panel.csv` | Crimes against women and cyber crimes: totals, rates, and the main crime heads |
| `state_cyber_sexual_abusive.csv` | Cyber crimes that are sexual or abusive in nature |
| `state_crimeheads_long.csv` | Every crime head parsed from the source tables, in long format (`year, state, category, table, crime_head, measure, key, value, source_file`). Use it for heads not in the two wide files, or for victims (`measure = victims`) and rates. |

**Empty cell = not published for that year** at State/UT level (see coverage below), not zero.

## 1. `state_women_cyber_panel.csv`

### Crimes against women
| Column | Years | Notes |
|---|---|---|
| `women_total_cases` | 2012–2024 | Total crime against women (IPC + SLL) |
| `female_population_lakh`, `women_crime_rate` | 2017–2024 | Rate = cases per lakh female population (NCRB's own figure) |
| `women_chargesheeting_rate` | 2020–2024 | % |
| `women_ipc_total`, `women_sll_total` | 2016–2024 | IPC (IPC/BNS in 2024) and special & local laws |
| `rape` | 2012–2024 | Sec 376 IPC / BNS 64–68, 70–71 |
| `rape_women_18plus`, `rape_girls_under18` | 2017–2024 | |
| `attempt_to_rape`, `murder_with_rape` | 2012– / 2017–2024 | |
| `dowry_deaths`, `abetment_of_suicide_of_women`, `cruelty_by_husband_or_relatives` | 2012–2024 | 304B, 306, 498A IPC (BNS 80, 108, 85) |
| `acid_attack`, `attempt_acid_attack` | 2017–2024 | `acid_attack_incl_attempt` adds 2016, when NCRB reported them together |
| `kidnapping_abduction_of_women` | 2012–2024 | see 2024 note |
| `kidnapping_to_compel_marriage` | 2016–2024 | Sec 366 IPC / BNS 87 |
| `assault_outrage_modesty_354_incl_354a_d` | 2012–2024 | **Use this for trends.** Sec 354 with 354A–D (sexual harassment, disrobing, voyeurism, stalking) |
| `assault_outrage_modesty_354_as_reported` | 2012–2024 | NCRB's own head. Equal to the above except 2024, when it is BNS 74 / Sec 354 only |
| `sexual_harassment_354a`, `assault_to_disrobe_354b`, `voyeurism_354c`, `stalking_354d` | 2016, 2024 | Not split out in the 2017–2023 state tables |
| `insult_to_modesty_509` | 2012–2024 | |
| `human_trafficking_370` | 2016–2023 | Dropped from the 2024 women table |
| `procuration_of_minor_girls`, `selling_of_girls`, `buying_of_girls` | 2017–2024 | `importation_of_girls`: 2012–2015, 2017–2024 |
| `dowry_prohibition_act`, `domestic_violence_act`, `indecent_representation_act` | 2012–2024 | |
| `immoral_traffic_act` | 2016–2024 | Women-victim cases only |
| `pocso_girl_victims` | 2017–2024 | POCSO cases with girl victims |
| `women_centric_cyber_crimes` | 2017–2024 | Cyber crimes counted within crime against women |
| `sexual_intercourse_by_deceit_bns69` | 2024 | New BNS offence |

### Cyber crimes
| Column | Years | Notes |
|---|---|---|
| `cyber_total_cases` | 2012–2024 | 2012–2013 = IT Act + IPC (SLL cyber crimes were not counted then) |
| `population_lakh`, `cyber_crime_rate` | 2016–2024 | Cases per lakh population |
| `cyber_chargesheeting_rate` | 2020–2024 | % |
| `cyber_it_act_total`, `cyber_ipc_total` | 2012–2014, 2016–2024 | |
| `cyber_sll_total` | 2014, 2016–2024 | |
| `cyber_fraud` | 2017–2024 | Sec 420 r/w 465, 468–471 IPC (BNS 318(4) etc.) |
| `cyber_criminal_breach_of_trust_fraud` | 2013–2014, 2016 | NCRB's pre-2017 "fraud" head (Sec 406–409). **Not comparable with `cyber_fraud`.** |
| `cyber_cheating`, `cyber_forgery`, `cyber_data_theft`, `cyber_computer_related_offences_66` | 2014, 2016–2024 (forgery from 2013) | |
| `cyber_identity_theft_66c`, `cyber_cheating_by_personation_66d` | 2016–2024 | |
| `cyber_fake_news` | 2017–2024 | |
| `cyber_sexual_abusive_total` | 2017–2024 | Same as in file 2 |
| `cyber_crimes_against_women`, `cyber_crimes_against_children` | 2017–2024 | Victim-based totals (tables 9A.10, 9A.11) |

## 2. `state_cyber_sexual_abusive.csv`

The columns come in four blocks. **Add up only within a block.** The `vs_women_*`,
`vs_children_*` and `caw_*` blocks are subsets of the offence-based block,
broken down by victim.

**A. By offence, all victims** (Table 9A.2; 2016 and earlier from the PDF tables).
NCRB counts each case once, under its principal offence, so these heads do not
overlap.

| Column | Years | Definition |
|---|---|---|
| `sexual_abusive_total` | 2017–2024 | `sexual_content_total + abusive_total` |
| `sexual_abusive_share_pct` | 2017–2024 | % of `cyber_total_cases` |
| `sexual_content_total` | 2013–2014, 2016–2024 | IT Act Sec 67 + 67A + 67B + other Sec 67 (i.e. `it67_all_subsections − it67c`) + Sec 66E. For 2013–2014 this is Sec 67 only (66E not reported separately) |
| `abusive_total` | 2017–2024 | Cyber stalking/bullying + blackmailing/threatening + defamation/morphing + fake profile + online abetment of suicide + (2024) BNS 69 |
| `it67_all_subsections` | 2013–2014, 2016–2024 | Publishing/transmitting obscene or sexually explicit material, all of Sec 67 |
| `it67_obscene_material` | 2017–2024 | Sec 67 |
| `it67a_sexually_explicit_material` | 2016–2024 | Sec 67A |
| `it67b_child_sexual_abuse_material` | 2016–2024 | Sec 67B |
| `it67_other_subsections`, `it67c_retention_by_intermediaries` | 2017– / 2016–2024 | 67C is data retention, **excluded** from `sexual_content_total` |
| `it66e_violation_of_privacy` | 2016–2024 | Capturing/publishing images of private areas |
| `cyber_stalking_bullying` | 2017–2024 | Sec 354D IPC / BNS 78 r/w IT Act |
| `cyber_blackmail_threatening` | 2017–2024 | Sec 503, 506, 384 IPC / BNS 351, 308 |
| `defamation_morphing` | 2017–2024 | Sec 469 IPC / BNS 336(4) and Indecent Representation of Women Act |
| `fake_profile` | 2017–2024 | |
| `abetment_of_suicide_online` | 2017–2024 | |
| `sexual_intercourse_by_deceit_bns69` | 2024 | |

**B. Cyber crimes against women** (Table 9A.10, 2017–2024): `vs_women_total`,
`vs_women_blackmail_threatening`, `vs_women_pornography_obscene_material`,
`vs_women_stalking_bullying`, `vs_women_defamation_morphing`,
`vs_women_fake_profile`, `vs_women_sexual_intercourse_by_deceit` (2024),
`vs_women_other`.

**C. Cyber crimes against children** (Table 9A.11, 2017–2024): `vs_children_total`,
`vs_children_blackmail_harassment`, `vs_children_sexual_abuse_material` (Sec 67B),
`vs_children_stalking_bullying`, `vs_children_fake_profile`,
`vs_children_online_games_gaming_apps`, `vs_children_other`.

**D. From the crime-against-women table** (3A.2): `caw_women_centric_cyber_total`
(2017–2024) and `caw_sexually_explicit_67a_67b` (2016–2024; 2016 is Sec 67A only).

## Sources by year

| Year | Women: totals | Women: crime heads | Cyber: totals | Cyber: crime heads |
|---|---|---|---|---|
| 2012 | CII 2015 State-wise 2001–2015 file (Excel) | same | Table 18.1 (PDF) | — |
| 2013 | same | same | Table 18.1 (PDF) | Tables 18.6, 18.7 (PDF) |
| 2014 | same | same | CII 2015 cyber 2014 file (Excel) | same |
| 2015 | same | same | Table 9A.1 of CII 2017 (Excel) | — not published by state |
| 2016 | Table 3A.1 of CII 2017 (Excel) | Table 3A.2 (PDF) | Table 9A.1 of CII 2017; rate from 9A.1 2016 (PDF) | Tables 9A.2(i)–(iii) (PDF) |
| 2017–2024 | Table 3A.1 (Excel) | Table 3A.2 (Excel; **2019 from PDF**) | Table 9A.1 (Excel) | Tables 9A.2, 9A.10, 9A.11 (Excel) |

For 2012–2015, NCRB's file has no aggregate rows, so `Total (States)`,
`Total (UTs)` and `All India` are sums of the State/UT rows. They match NCRB's
published national totals (244,270; 309,546; 337,922; 327,394).

## Things to know before comparing years

**Problems in NCRB's own files**
- **Wrong 2019 file on NCRB's site:** the 2019 Excel link for Table 3A.2 serves the 2020 file. 2019 crime heads were taken from the 2019 PDF instead.
- **Wrong 2012 cyber files on NCRB's site:** the 2012 links for cyber Tables 18.6/18.7 serve the 2013 files. So 2012 has cyber totals but no crime heads.

**Legal changes**
- **2013 Criminal Law (Amendment) Act:** added Sec 354A–D and widened the definition of rape. Sec 354 counts jump between 2012 and 2013.
- **From 2017, POCSO cases with girl victims count as crime against women:** this raises `women_total_cases`. Rape of girls under 18 is increasingly booked under POCSO, which is why `rape_girls_under18` falls.
- **2024 (IPC → BNS from 1 July 2024):** 2024 tables combine IPC and BNS cases.
  - Sec 354A–D are reported separately in 2024, so use `assault_outrage_modesty_354_incl_354a_d`.
  - Sec 366 (kidnapping to compel marriage) is no longer inside `kidnapping_abduction_of_women`.
  - Sec 370 trafficking is not in the 2024 women table.

**Definition changes**
- **Cyber "fraud":** before 2017 it meant criminal breach of trust (Sec 406–409); from 2017 it means Sec 420-type fraud. The two are kept in separate columns.

**Boundary changes**
- **Andhra Pradesh and Telangana:** Telangana is separate from 2014. For 2012–2013, Andhra Pradesh includes it.
- **Jammu & Kashmir and Ladakh:** Ladakh is separate from 2020. Up to 2019, Jammu & Kashmir includes it.
- **D&N Haveli and Daman & Diu:** reported separately up to 2019 and as `D&N Haveli and Daman & Diu` from 2020.

**Rates**
- Rates come from NCRB's own tables and use each edition's population projections, so they are not recomputed here.
- To build rates for other years or columns, divide by a consistent population series.
