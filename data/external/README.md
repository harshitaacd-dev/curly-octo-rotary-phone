# External sources

- `LS438_02122025.pdf`: Lok Sabha Unstarred Question No. 438, answered 2 December 2025
  by the Ministry of Home Affairs ("Rise in cybercrime cases"). Downloaded from
  https://www.mha.gov.in/MHA1/Par2017/pdfs/par2025-pdfs/LS02122025/438.pdf
  - Annexure I: all-India cyber crimes by crime head, 2014–2023, parsed into
    `data/clean/national_cyber_crimeheads_2014_2023.csv` by `scripts/parse_ls438.py`.
  - Annexure II: State/UT totals for 2014–2023.
- `trai/`: TRAI quarterly *Performance Indicator Reports*, December quarter 2004–2025 plus
  June 2026 — internet subscribers, national and (from Dec 2021) by State/UT. Sources, series
  breaks and caveats in `trai/README.md`; parsed by `scripts/internet_trai.py`.
- `surveys/`: page extracts of NSS 2017-18 (Report 585), NFHS-5 2019-21 and CAMS 2022-23
  (Report 590), plus the CMS: Telecom 2025 press note — internet use by State/UT, age and
  gender. Details in `surveys/README.md`; parsed by `scripts/internet_surveys.py`.
