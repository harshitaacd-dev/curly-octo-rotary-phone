# Household surveys: internet use by State/UT, age and gender

Page extracts (cover page + the tables used) of official survey reports, parsed by
`python scripts/internet_surveys.py data/external/surveys data/clean/internet_use_surveys_long.csv`.

| File | Survey | Pages kept | Full report |
|---|---|---|---|
| `nss75_2017_18_internet_tables.pdf` | NSS 75th round, *Household Social Consumption on Education in India*, Report 585 (July 2017–June 2018) | cover; Statements 7.5.1, 7.6.1 (State × gender × sector, age 5+); Table 18 (all-India × age × gender × sector) | https://mospi.gov.in/sites/default/files/publication_reports/Report_585_75th_round_Education_final_1507_0.pdf |
| `nfhs5_2019_21_tables3_6_3_7.pdf` | National Family Health Survey (NFHS-5) 2019-21, India Report | cover; Table 3.6 (age × gender), Table 3.7 (State × gender), ages 15-49 | https://dhsprogram.com/pubs/pdf/FR375/FR375.pdf |
| `cams_2022_23_tables16_17.pdf` | Comprehensive Annual Modular Survey (CAMS), NSS 79th round, Report 590 (July 2022–June 2023) | cover; Tables 16 (able to use internet) and 17 (used internet in last 3 months), State × age (15-24, 15-29, 15+) × gender × sector | https://www.mospi.gov.in/sites/default/files/publication_reports/CAMS%20Report_October_N.pdf |
| `cms_telecom_2025_press_note.pdf` | Comprehensive Modular Survey: Telecom, Jan–Mar 2025, press note (29 May 2025); all-India only, typed into the script | whole note | https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/may/doc2025529560001.pdf |

## Definitions (not comparable across surveys)

| Survey | Indicator | Population |
|---|---|---|
| NSS 2017-18 | used internet in the last 30 days; able to use internet | age 5+ (Table 18 also by age group). "Male" includes transgender. Major States only; rural Delhi not shown. |
| NFHS-5 2019-21 | ever used the internet | women and men age 15-49 |
| CAMS 2022-23 | used internet at least once in the last 3 months (any device, place, purpose); able to use internet | age 15-24, 15-29, 15+ |
| CMS: Telecom 2025 | as CAMS | all-India only; State estimates not released |

State × age × gender together is published only by CAMS 2022-23. Other cross-tabs need unit-level
data (microdata.gov.in for NSS/CAMS, dhsprogram.com for NFHS), which requires registration.
