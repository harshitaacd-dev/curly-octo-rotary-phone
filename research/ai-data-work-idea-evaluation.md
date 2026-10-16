# Idea Evaluation: Women Doing AI Data Work in South Asia

*Produced with the `idea-evaluator` skill, using the economics evaluation criteria. Where sources were journalism or industry reports rather than peer-reviewed research, this is stated.*

**Original idea:** "A large amount of data labelling work is done by South Asian women to fuel the current AI boom. It is extractive and underpaid."

**Questions asked:** (1) Is this research feasible, and what is the economics in it? (2) Are there datasets that would make it an econometrics paper?

## 1. First impression
- **Paper type:** a new problem in a new setting. AI data work has been studied by sociologists and computer scientists, but almost never with econometrics.
- **Field:** economics (regressions, panel data, comparing groups).
- **One-sentence story as written:** two parts of it are claims that need proving, not starting facts: that the work is *mostly done by South Asian women*, and that it is *extractive*.

## 2. Serious problems

| # | Problem | Severity | Fix |
|---|---|---|---|
| 1 | **The premise is assumed, not measured.** The Online Labour Index estimates women are a minority of India's online freelancers, and research using CMIE household data finds platform work in India is overwhelmingly male. Women may still dominate certain annotation companies and rural centres (reporting on iMerit and rural Telangana suggests so). "Extractive" is a moral judgement that economists can't test until it is defined measurably. | MAJOR | Make the premise the first research question: *where* in the supply chain are women concentrated? Define "extractive" as (a) pay below a competitive wage because of employer power (monopsony), (b) pay below what the same women earn elsewhere, or (c) pay below what rich-country workers get for the same task. |
| 2 | **Data and cause-and-effect.** No official Indian survey identified AI annotators; India's PLFS adds platform/digital-work questions only from 2026. Women who take up this work are self-selected. | MAJOR | Combine a public dataset with platform data or a survey; choose one research design before collecting data. |

Neither problem kills the idea.

## 3. Fit with time and skills
User profile (given later): Master's student, medium econometrics skills with help available, **4 weeks**, **no fieldwork**.

- **Red** for the original causal idea (estimating employer pay-setting power needs platform or company data plus causal methods).
- **Green** for a narrower descriptive paper that decomposes the gender pay gap using a national survey.

## 4. Scores on the five economics criteria (each starts at 5)

| Criterion | Score | Reason | How to raise it |
|---|---|---|---|
| Credibility of cause and effect | 3 | No research design yet | Pick one: (a) generative-AI demand shock after 2022 × district exposure to annotation centres, using PLFS; (b) pay variation on a platform to compare how women vs men respond to pay; (c) the same task posted in several countries |
| Size of effect | 5 | No grounds yet | Report effects in rupees per hour or as a share of the competitive wage |
| New mechanism | 7 (reasoning, not yet data) | **Gendered monopsony:** women with mobility constraints and home duties have fewer alternatives, respond less to pay cuts, so employers can pay them further below the value of their work. Dube et al. (AER: Insights 2020) found substantial employer power even on Mechanical Turk. | Test whether women respond less to pay changes than men doing the same tasks |
| New data | 4 (public data only) / 8 (new data) | PLFS and Online Labour Index are public; a survey or company data would be a first | Partner with Karya, an annotation firm, or ILO researchers |
| Policy relevance | 7 | India's 2026 survey changes, Kenya's 2026 draft pay rules for data workers, Indian gig-worker social security laws | Frame results as concrete policy guidance |

## 5. Could it change the field?
- Challenges an assumption: **partly** (pushes back on "AI replaces labour").
- Tackles an avoided problem: **yes** (these workers are invisible in official statistics).
- Technology shift: **yes** (the generative-AI boom changed demand and gives a dated shock).
- Hamming's rule: **no**.

Potential to change the field: **possible**.

## 6. Feasibility
| Risk | Level | Mitigation |
|---|---|---|
| Computing | Low | Standard econometrics software |
| Data | High | See datasets below; budget for a survey or partnership if going beyond public data |
| Technical skills | Medium | Panel data and difference-in-differences; Python for scraping |
| Time | Medium | PLFS alone: 6–9 months for the full idea; adding a survey: 12–18 months |

## 7. Verdict
**Accept with revisions.** For a 4-week Master's project: do the narrower descriptive paper now; keep the employer-power idea for a PhD or later paper.

## The economics in it (answer to Q1)
- **Monopsony / wage markdown** (strongest): employers pay women less because women have fewer realistic alternatives.
- **Pay vs alternatives:** an ILO working paper found crowdworkers in middle-income countries earn less than rich-country peers but report *higher* satisfaction because their other options are worse. The work can be low-paid and still be the best option available. A good paper faces this tension directly.
- **Same work, different pay across countries:** an ILO presentation reports US Mechanical Turk workers earning about 2.5 times Indian workers' hourly pay (from a talk; verify before citing).
- **Effects on women's employment and bargaining power:** see Ho, Jalota & Karandikar's West Bengal experiment, where allowing work from home roughly tripled job take-up.

*Correction:* an earlier version of this answer attributed the "tripled take-up" result to a J-PAL evaluation of Karya. It comes from Ho, Jalota & Karandikar (data-entry jobs, West Bengal). No published randomised evaluation of Karya's earnings effects was found.

## Datasets (answer to Q2)

| Dataset | What it gives | Access |
|---|---|---|
| PLFS (India's national labour survey) | Earnings of comparable women by district and education; platform-worker questions from 2026 | Free microdata, MoSPI |
| CMIE Consumer Pyramids (CPHS) | Household panel used to study platform workers | Paid; many universities subscribe |
| Online Labour Index / Online Labour Observatory | Online freelance work by country, occupation, gender (gender guessed from names) | Free download |
| ILO crowdwork surveys | Pay, hours, demographics of microtask workers incl. India | Ask the ILO; access unconfirmed |
| Scraped freelance profiles (e.g. Upwork) | Hourly rates by gender and country (method: Foong et al., CSCW 2018) | Build yourself; check terms of service |
| Fairwork Cloudwork Ratings | Yearly platform fairness scores | Free |
| WageIndicator | Living-wage benchmarks; small 2026 Kenya data-worker survey | Free / on request |
| Company filings, NASSCOM, TeamLease | Industry size, value captured by each tier | Public but patchy |
| Own survey or partner data (Karya, annotation firm) | Pay, hours, gender, alternatives together | Needs ethics approval and partnership |
| **Pakistan Labour Force Survey 2024–25** | First South Asian national survey identifying digital workers (Shoib & Lohana 2026 find a 22.5% earnings penalty for women) | Request from Pakistan Bureau of Statistics; release speed unverified |

## Sources
- [Online Labour Index 2020 (HIIG)](https://www.hiig.de/en/publication/online-labour-index-2020-new-ways-to-measure-the-worlds-remote-freelancing-market/), [Online Labour Observatory](https://onlinelabourobservatory.org/paper/intro-oli2020/)
- [Dube, Jacobs, Naidu & Suri, Monopsony in Online Labor Markets](https://www.aeaweb.org/doi/10.1257/aeri.20180150)
- [ILO crowdwork working paper](https://webapps.ilo.org/static/english/intserv/working-papers/wp050/index.html), [CEU thesis on crowdwork in India](https://www.etd.ceu.edu/2020/gobel_nora.htm)
- [Ideas for India: platform economy statistics](https://www.ideasforindia.in/topics/productivity-innovation/collecting-labour-market-statistics-to-study-the-platform-economy.html), [Ideas for India: India's data workers](https://www.ideasforindia.in/topics/productivity-innovation/india-s-data-workers-the-human-labour-making-machines-learn)
- [Fairwork Cloudwork Ratings 2023](https://fair.work/en/fw/publications/fairwork-cloudwork-ratings-2023-work-in-the-planetary-labour-market/)
- [MIT Tech Review on impact sourcing](https://www.technologyreview.com/2019/08/07/133845/cloudfactory-ddd-samasource-imerit-impact-sourcing-companies-for-data-annotation/), [Fifty-Two: Human Touch](https://fiftytwo.in/story/human-touch/)
- [Foong et al. CSCW 2018](https://www.brenthecht.com/publications/cscw2018_upworkgender.pdf)
- [WageIndicator Kenya data workers survey](https://wageindicator.org/what-we-do/news-stories/meta-data-workers-kenya-survey), [Kenya draft rules](https://weetracker.com/2026/07/24/kenya-ai-minimum-pay-mental-healthcare-workers/)
- [Ho, Jalota & Karandikar, Bringing Work Home](https://steg.cepr.org/sites/default/files/2024-01/WP080_Ho_BringingWorkHome_0.pdf)
- [Shoib & Lohana, Pakistan LFS 2024–25 (MPRA)](https://mpra.ub.uni-muenchen.de/129903/)
