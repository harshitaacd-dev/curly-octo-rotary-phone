# Econometric Analysis of NCRB Cybercrime Data: Determinants Regressions Dominate, While the Methods That Work on NCRB Crime Data Have Not Yet Been Applied to Cybercrime

## Abstract

India's National Crime Records Bureau (NCRB) has published State-level cybercrime counts since the early 2010s, and registered cases rose several-fold over the decade to 2023. This review asks how that data has been analysed econometrically, what the wider econometric literature on NCRB crime data teaches about methods and measurement, and where a new study can contribute. We searched along five angles (econometric studies of NCRB cybercrime; econometric studies of NCRB crime generally; quasi-experimental designs on NCRB data; measurement and reporting; and cross-national cybercrime determinants) and verified 14 works (three at metadata level only). Three findings stand out. First, the econometric literature on NCRB cybercrime is thin and mostly asks which macroeconomic variables predict cybercrime. Its strongest study finds that cybercrime is highly persistent and that unemployment and inflation do not predict it, and it could not include internet penetration. Second, the most credible econometric work on NCRB data uses shocks or staggered policy rollouts, not determinants regressions, and two such studies show that NCRB counts of crimes against women respond strongly to how easy it is to report. Third, State determinants studies of NCRB crime find perverse or unstable deterrence effects, which is consistent with registered crime partly measuring police and reporting behaviour. No retrieved study applies a shock or rollout design to NCRB cybercrime, and none separates cybercrime against women from other cybercrime.

## 1. Introduction

NCRB's annual *Crime in India* reports count First Information Reports (FIRs) registered by police, by State and crime head. Cybercrime has its own chapter, with heads under the Information Technology Act, the Indian Penal Code (now the Bharatiya Nyaya Sanhita, BNS) and special laws, and from 2017 separate tables for cybercrimes against women and children. The series is long, public and State-level, which makes it attractive for panel econometrics. It also records police registration rather than victimisation, and its categories have changed several times.

This review answers three research questions:

- **RQ1.** Which studies have analysed NCRB cybercrime data econometrically, with what designs, and what did they find?
- **RQ2.** What does the econometric literature on NCRB crime data more broadly show about which designs are credible and how measurement problems affect results?
- **RQ3.** Where does a study of technology shocks and cybercrime against women fit, and what gaps remain?

Section 2 describes the search, Section 3 lays out how the literature is organised, Sections 4 to 6 develop the evidence, Section 7 compares across branches, Section 8 lists open problems, and Section 9 answers the research questions.

## 2. Methodology

**Search angles.** (a) Econometric and statistical studies of NCRB cybercrime; (b) econometric determinants studies of NCRB crime; (c) quasi-experimental studies using NCRB data; (d) measurement, under-reporting and victim surveys; (e) cross-national determinants of cybercrime. Angles were run one after another by a single researcher.

**Keyword groups.** NCRB cyber crime + panel / regression / determinants / internet penetration; cybercrime India + state-level + GMM / fixed effects; NCRB + under-reporting / victimisation survey; NCRB + district + rainfall / reservation / police stations; routine activity theory + cybercrime + countries.

**Time range.** 2012–2026.

**Inclusion.** Journal articles, working papers and institutional reports whose existence and main finding we confirmed. Three works are cited at metadata level because their full author lists, titles or texts were not retrievable (marked in the references). **Exclusion.** Journalism and exam-preparation sites, used only for context; descriptive papers without any statistical analysis; and works whose existence or authorship could not be confirmed (including an arXiv survey of Indian cybercrime and a 2016 article on cybercrime in India in *Crime, Law and Social Change*).

**Final corpus.** 14 works.

| Evidence type | What it is | Credibility for causal claims |
|---|---|---|
| Quasi-experiments on NCRB data | Rainfall shocks, staggered reservations or police-station openings, with State or district fixed effects | Strongest available |
| Dynamic panel / determinants regressions | System GMM or panel-corrected regressions of crime rates on socioeconomic covariates | Weak: covariates are endogenous and reporting is uncontrolled |
| Time-series forecasting | ARIMA models of State cybercrime | Descriptive only |
| Correlation of trends | Cybercrime counts against internet subscribers | Descriptive only |
| Victim surveys | Surveys of cybercrime victims or crime victims generally | Strong on reporting gaps; not panel data |

## 3. How the literature is organised

We sort the literature by **what question a study asks** (what predicts crime levels; what a shock or policy does; how well the data measures crime) and **which data it uses** (NCRB cybercrime; other NCRB crime; non-Indian cybercrime).

| | NCRB cybercrime | Other NCRB crime | Cybercrime outside India |
|---|---|---|---|
| **What predicts crime levels** | [1], [2], [3] | [4], [5] | [12], [13] |
| **Effect of a shock or policy** | (none) | [6], [7], [8], [9] | [14] |
| **How well the data measures crime** | [11] | [6], [7], [10] | (none) |

The empty cell is the main finding: **no retrieved study estimates the effect of a shock or policy on NCRB cybercrime.** The two NCRB reporting studies [6], [7] straddle categories, because their designs estimate effects and, in doing so, reveal how the data measures crime.

## 4. Econometric work on NCRB cybercrime: determinants and persistence (RQ1)

Three works analyse NCRB cybercrime statistically, and they differ mainly in how much they try to explain. The most rigorous is a 2025 study in *Safer Communities* [1], which uses a two-step system GMM estimator on 29 States and union territories for 2017–2022. It finds that cybercrime is strongly persistent from year to year and that unemployment, inflation and education spending are not significant drivers. Internet penetration was left out because State data was unavailable, so the study cannot test the most obvious explanation. Bora, Nayak and Kulsrestha [2] take the opposite approach: they set national NCRB counts against TRAI internet subscriber numbers and report a strong correlation, but the method is a correlation of two rising series, which any two upward trends would satisfy. A Madras School of Economics dissertation [3] fits ARIMA models to State cybercrime series for the largest-reporting States, which describes and forecasts trends but does not explain them.

| Study | Data | Method | Main result | Internet access included? |
|---|---|---|---|---|
| *Safer Communities* study [1] | 29 States, 2017–2022 | System GMM | Strong persistence; macro variables not significant | No (data unavailable) |
| Bora et al. [2] | National, 2014–2023 | Correlation with TRAI subscribers | Cybercrime rises with subscribers | Yes, national only |
| Seby [3] | Top States, time series | ARIMA | Trend description and forecasts | No |

*Table 1. Econometric work on NCRB cybercrime asks what predicts crime levels; none uses State internet access and a credible design together.*

The persistence result in [1] has two readings, and the data cannot yet tell them apart. It may mean cybercrime builds on itself (offender networks, learned techniques). Or it may mean State registration practices, such as whether dedicated cyber police stations exist, are stable, so the lagged count predicts the current one. The second reading links directly to Section 6.

## 5. Econometric work on other NCRB crime: determinants are unstable, shock designs are credible (RQ2)

Determinants studies of NCRB crime generally run into the same problem as [1]. Hazra [4] studies 32 States and union territories for 2010–2016 with panel-corrected standard errors and finds that population density, poverty, inequality, literacy and GSDP per capita explain crime rates, along with chargesheeting and conviction rates. Raj and Rahman [5], using system GMM on 2001–2014 State data, find that the probability of arrest has a *perverse* effect: more arrests go with more crime. The two studies disagree on deterrence, and the condition that best explains the disagreement is measurement. If police who arrest more also register more FIRs, arrest rates and registered crime move together regardless of deterrence. Neither study can separate these, because neither has a source of variation outside the system.

The studies that do have such variation produce findings that hold up. Sekhri and Storeygard [8] use rainfall shocks across 583 districts for 2002–2007 and find that a one standard deviation drop in rainfall raises reported dowry deaths by 7.8%, with no comparable pattern in other crimes. Blakeslee and Fishman [9] use weather shocks over 1971–2000 and find that drought and heat raise nearly every crime category, property crime most. Iyer, Mani, Mishra and Topalova [6] exploit the staggered timing of quotas for women in local councils and find recorded crimes against women rose with no rise in crimes against men, which they attribute mainly to more reporting. Amaral, Bhalotra and Prakash [7] use the staggered opening of women-only police stations and find a 29% rise in recorded crimes against women, driven by domestic violence, with no change in femicide or survey-reported violence, again a reporting effect.

| Study | Variation used | NCRB outcome | Result | Reporting addressed? |
|---|---|---|---|---|
| Hazra [4] | None (determinants) | Crime rates by type | Socioeconomic and deterrence variables matter | No |
| Raj & Rahman [5] | None (system GMM) | Crime rates | Perverse deterrence | No |
| Sekhri & Storeygard [8] | Rainfall shocks | Dowry deaths | +7.8% per SD rainfall drop | Partly (placebo crimes) |
| Blakeslee & Fishman [9] | Weather shocks | All crime types | Drought and heat raise crime | Partly |
| Iyer et al. [6] | Staggered council quotas | Crimes against women | Rise, mainly reporting | Yes (crimes against men as comparison) |
| Amaral et al. [7] | Staggered women's police stations | Crimes against women | +29%, reporting | Yes (femicide, surveys) |

*Table 2. Studies with an outside source of variation and a comparison crime produce interpretable results; determinants regressions disagree with each other.*

## 6. Measurement: NCRB counts police registration, and cybercrime is under-registered (RQ2)

NCRB records FIRs, and only the principal offence of each FIR. Commentary on the latest reports notes that a fall in registered crime can reflect police practice rather than less crime [10]. For cybercrime specifically, the *Status of Policing in India Report 2026* by Common Cause and Lokniti-CSDS [11] surveyed 8,306 people in 16 States about how cybercrime victims seek redress through the police. It reports that women, poorer and rural victims rely more on informal channels, and that informal routes such as personal contacts go with higher recovery of lost money. If registration depends on who the victim is, State cybercrime counts partly measure access to police. That is the same mechanism [6] and [7] found for offline crimes against women.

Two features of the cyber series make this worse. Financial fraud makes up most registered cybercrime in recent years, so totals mostly track fraud, not abuse. And the categories change: cybercrimes against women are reported separately only from 2017, and from July 2024 offences moved from the IPC to the BNS.

Outside India, cross-national studies of cybercrime determinants use routine activity theory: Kigerl [12] studies which countries host high cybercrime, and his later study [13] of 871,146 spam messages from 120 countries finds that internet users per capita predicts malware, fraud and spam. These studies measure cybercrime from technical traces rather than police records, which avoids the registration problem but does not exist at Indian State level.

## 7. Comparing across the branches

**The same data, two traditions.** NCRB cybercrime has been studied only with determinants regressions [1], [2], [3], while other NCRB crime has been studied with both determinants regressions [4], [5] and shock or rollout designs [6]–[9]. The shock designs give results that hold up and agree with each other; the determinants regressions disagree on something as basic as deterrence. The cybercrime literature has so far followed the weaker tradition.

**Reporting runs through every branch.** The persistence in [1], the perverse deterrence in [5] and the reporting effects in [6] and [7] all fit one explanation: registered crime partly measures police and victim behaviour. The two studies that handle this well do it with a *comparison crime* (crimes against men in [6]; femicide and survey-reported violence in [7]). For cybercrime, the natural comparisons are offline crimes against women in the same State, and cyber fraud as an online crime not aimed at women.

**The access variable is missing where it matters.** The most rigorous cybercrime study [1] could not include internet access; the one that did [2] used national data only. The cross-national literature [13] suggests internet use per capita is the first variable to test. State access data now exists (NSS 2017-18, NFHS-5, CAMS 2022-23, TRAI subscriptions from 2021), so this gap can be closed.

## 8. Open problems and future directions

1. **A shock or rollout design on NCRB cybercrime.** The empty cell in Section 3. Candidate sources of variation: the generative-AI boom (2023), with State exposure from internet access or search data; the staggered opening of State cyber police stations; and the 2019 national cybercrime reporting portal.
2. **Separating cybercrime against women from cybercrime generally.** No retrieved econometric study uses the post-2017 tables of cybercrimes against women. Comparing them with offline crimes against women and with cyber fraud would separate gendered abuse, general online-crime growth and State reporting.
3. **Testing the persistence result.** Whether persistence [1] reflects offending or stable registration practice could be tested by checking whether persistence changes when cyber police stations open [unconfirmed: no State-level data on cyber police station openings was retrieved].
4. **Linking victim surveys to NCRB counts.** The SPIR 2026 survey [11] covers 16 States; comparing its State estimates of cybercrime victimisation with NCRB registrations would measure under-registration directly.

## 9. Conclusion

**RQ1.** Three studies analyse NCRB cybercrime statistically: a system GMM determinants study [1], which finds strong persistence and no role for unemployment or inflation but omits internet access; a national correlation with internet subscribers [2]; and ARIMA forecasting [3]. None uses an outside source of variation, and none studies cybercrime against women separately.

**RQ2.** On NCRB crime generally, determinants regressions give unstable results, including perverse deterrence [4], [5], while designs using rainfall shocks or staggered policies [6]–[9] give credible ones. Two of those designs show that NCRB counts of crimes against women respond strongly to how easy reporting is [6], [7], and a 2026 victim survey suggests cybercrime registration depends on who the victim is [11].

**RQ3.** A study of technology shocks and cybercrime against women would be the first to bring the shock-and-comparison tradition to NCRB cybercrime. Its contributions would be State internet access as a regressor, which [1] lacked; the post-2017 tables of cybercrimes against women, which no retrieved study uses; and comparison crimes to separate abuse from reporting, following [6] and [7].

**This review's contribution** is to show that econometric work on NCRB cybercrime has so far asked the question NCRB data answers least reliably (what predicts crime levels), while the question it answers best (how crime responds to a shock, relative to a comparison crime) has not yet been asked of cybercrime.

## References

[1] [Authors not retrieved], "Economic Determinants of Cybercrime in India: A State-Level Panel Data Analysis," Safer Communities, 2025. *(Abstract-level; full text and author list not retrieved.)*
[2] Bora, Nayak, Kulsrestha, "Growing Incidence of Cybercrime in India: Causes and Remedies," JASSH (Krrish Publications), 2026.
[3] A. Seby, Master's (AQF) dissertation on ARIMA time-series analysis of cybercrime in Indian States, Madras School of Economics. *(Exact title and year not retrieved.)*
[4] D. Hazra, "What Does (and Does Not) Affect Crime in India?," International Journal of Social Economics, 2020.
[5] P. Raj, M. M. Rahman, "Revisiting the Economic Theory of Crime: A State-Level Analysis in India," Cogent Social Sciences, 2023.
[6] L. Iyer, A. Mani, P. Mishra, et al., "The Power of Political Voice: Women's Political Representation and Crime in India," American Economic Journal: Applied Economics, 2012.
[7] S. Amaral, S. Bhalotra, N. Prakash, "Gender, Crime and Punishment: Evidence from Women Police Stations in India," IZA Discussion Paper 14250, 2021.
[8] S. Sekhri, A. Storeygard, "Dowry Deaths: Response to Weather Variability in India," Journal of Development Economics, 2014.
[9] D. S. Blakeslee, R. Fishman, "Weather Shocks, Agriculture, and Crime: Evidence from India," Journal of Human Resources, 2018.
[10] R. Jha, "Measuring Crime in India: The Limits of Statistical Compilation," Observer Research Foundation, Expert Speak, 2026. *(Year inferred from the NCRB edition it discusses.)*
[11] Common Cause, Lokniti-CSDS, "Status of Policing in India Report 2026: Cybercrime – Victim Perspectives," Common Cause, 2026. *(Summarised from secondary coverage.)*
[12] A. Kigerl, "Routine Activity Theory and the Determinants of High Cybercrime Countries," Social Science Computer Review, 2012.
[13] A. Kigerl, "Routine Activity Theory and Malware, Fraud, and Spam at the National Level," Crime, Law and Social Change, 2021.
[14] M. Bhuller, T. Havnes, E. Leuven, et al., "Broadband Internet: An Information Superhighway to Sex Crime?," Review of Economic Studies, 2013.
