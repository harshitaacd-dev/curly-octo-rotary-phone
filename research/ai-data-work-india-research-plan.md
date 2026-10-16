# Research Plan: Women in AI Data Work in India (4-Week Master's Project)

**Constraints:** India only; focus on women workers and AI annotation/labelling work; Master's level, medium econometrics with help available, 4 weeks, no fieldwork.

## The core limitation
No Indian dataset directly identifies AI annotators. The 2026 PLFS round reportedly adds digital/platform-work questions, but its microdata won't be available in time. So the project studies women in **data work**, the job category AI annotation falls under, using codes the surveys already record. State this proxy clearly in the write-up.

## Identifying data workers in Indian surveys

| Code | Meaning | Why it fits |
|---|---|---|
| Industry (NIC-2008) **6311** | Data processing, hosting and related activities | Indian annotation companies typically register here |
| Occupation (NCO-2015) **4132** | Data entry clerks | Closest occupation to annotation |
| Occupation (NCO-2015) **4131** | Typists and word processing operators | Wider net, for robustness |

## Datasets

| Dataset | What it gives | Access | Role |
|---|---|---|---|
| **PLFS 2017-18 to 2023-24** (main) | Gender, earnings, hours, industry/occupation codes, district, urban/rural, working from home, written contract, paid leave, social security | Free unit data, MoSPI (microdata.gov.in) | Core analysis |
| **ASUSE** (unincorporated enterprises survey) | Small and home-based businesses in data processing, owner gender, hired workers | Free, MoSPI | Covers the informal, home-based segment |
| **Online Labour Index** | India's online freelance work by occupation and gender (names-based), daily | Free | Platform-side figures before vs after ChatGPT |
| **CAMS 2022-23** | Digital skills by gender and district | Free, MoSPI | Where women have skills for this work |

## Research questions

1. **(Recommended main question) Who are India's women data workers, and are they underpaid compared to their alternatives?** Pool PLFS rounds; keep data workers via the codes above. Compare women with men in data work, and with women in other office and service jobs, on earnings, hours, working from home and job quality. Run an Oaxaca–Blinder decomposition to split the gender gap into explained (education, location, occupation) and unexplained parts. This makes "underpaid" measurable.
2. **Is data work worse quality for women?** Combine PLFS questions on written contracts, paid leave and social security into a job-quality score. This makes "extractive" measurable without data on the value workers produce.
3. **Did the generative-AI boom change women's data work?** Track women's share and pay in NIC 6311 before and after 2022, compared with the rest of IT services (NIC 62). Only one or two post-2022 rounds, so this is a trend comparison, not causal. Use as a secondary section.
4. **Home-based data work: a way in, or a pay penalty?** Compare pay for women doing data work from home vs at a workplace (links to Ho, Jalota & Karandikar's West Bengal experiment).

**Recommendation:** Q1 as the main paper, Q2 as a second results section, Q3 briefly as an extension.

## Biggest risk
Too few women in these codes. Check on day 1: count women in NIC 6311 or NCO 4132 per round.
- Fewer than a few hundred → pool rounds and use the wider occupation definition.
- Still too few → broaden to women in data processing and other back-office services.

## Schedule
1. **Week 1:** download PLFS, check sample sizes, build variables.
2. **Week 2:** descriptive tables and wage regressions.
3. **Week 3:** decomposition, job-quality score, robustness checks.
4. **Week 4:** write up (background section can draw on `ai-data-work-south-asia-literature-review.md`).

## Alternative considered: Pakistan
Pakistan's Labour Force Survey 2024–25 identifies digital workers directly (see Shoib & Lohana 2026). A wage regression plus Oaxaca–Blinder decomposition would extend their paper. Risk: microdata release speed is unverified. Dropped in favour of India-only scope.
