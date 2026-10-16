# TRAI Performance Indicator Reports (internet subscribers)

The Telecom Regulatory Authority of India's quarterly *Indian Telecom Services Performance
Indicators* report for the **October–December quarter of each year, 2004–2025**, plus the latest
one (**April–June 2026**). Listed at
https://www.trai.gov.in/release-publication/reports/performance-indicators-reports

Parsed by `python scripts/internet_trai.py data/external/trai data/clean` into
`data/clean/india_internet_trai.csv` (national) and `data/clean/state_internet_trai.csv`
(State/UT, Dec 2021 onwards).

| Data as of | File | Source |
|---|---|---|
| Dec 2004 | `qpir_dec_2004.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/report22mar05.pdf |
| Dec 2005 | `qpir_dec_2005.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/ReportQEDec-05Part1.pdf |
| Dec 2006 | `qpir_dec_2006.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Report1.pdf |
| Dec 2007 | `qpir_dec_2007.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/preport10april08.pdf |
| Dec 2008 | `qpir_dec_2008.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Report1apr09.pdf |
| Dec 2009 | `qpir_dec_2009.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/IndicatorReport6apr10.pdf |
| Dec 2010 | `qpir_dec_2010.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Indicator_Report_Dec-10.pdf |
| Dec 2011 | `qpir_dec_2011.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Indicator%20Report-dec-2011.pdf |
| Dec 2012 | `qpir_dec_2012.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Indicator%20Reports%20-%20Dec-12.pdf |
| Dec 2013 | `qpir_dec_2013.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Indicator%20Reports%20-%20Dec-2013.pdf |
| Dec 2014 | `qpir_dec_2014.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Indicator_Reports%20-%20Dec-14%3D08052015.pdf |
| Dec 2015 | `qpir_dec_2015.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/QPIR_Oct_to_Dec-15.pdf |
| Dec 2016 | `qpir_dec_2016.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/Indicator_Reports_Dec_16_07042017.pdf |
| Dec 2017 | `qpir_dec_2017.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/PIRReportsDec26032018.pdf |
| Dec 2018 | `qpir_dec_2018.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/PIR_04042019_0.pdf |
| Dec 2019 | `qpir_dec_2019.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/PIR_30062020.pdf |
| Dec 2020 | `qpir_dec_2020.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/QPIR_27042021_0.pdf |
| Dec 2021 | `qpir_dec_2021.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/QPIR_05052022.pdf |
| Dec 2022 | `qpir_dec_2022.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/QPIR_31052023_0.pdf |
| Dec 2023 | `qpir_dec_2023.pdf` | https://www.trai.gov.in/sites/default/files/2024-09/QPIR_23042024_0.pdf |
| Dec 2024 | `qpir_dec_2024.pdf` | https://www.trai.gov.in/sites/default/files/2025-04/QPIR-Dec-24%2024_04.pdf |
| Dec 2025 | `qpir_dec_2025.pdf` | https://www.trai.gov.in/sites/default/files/2026-03/QPIR_03032026_0.pdf |
| Jun 2026 | `qpir_jun_2026.pdf` | https://www.trai.gov.in/sites/default/files/2026-10/QPIR_12102026.pdf |

## Reading the numbers

- **Subscriptions, not people.** TRAI counts internet connections reported by operators. One
  person with two SIMs counts twice, so per-100 figures can exceed 100 (Delhi ~176–210, Goa
  ~130–150). For "share of people online" use the World Bank/ITU series
  (`data/clean/india_internet_worldbank.csv`).
- **Break in 2013.** Up to Dec 2012 the total covers only wired and dongle/data-card internet
  (25 million in Dec 2012). Phones able to use data were reported separately as "wireless data
  subscribers" (kept in `wireless_data_capable_subs_mn`; it counts capable handsets, not users).
  From Dec 2013 the total includes internet on mobile phones (239 million). Do not compare across
  the break.
- **Broadband definition** rose from ≥256 kbps (to 2012) to ≥512 kbps (2013–2022) to ≥2 Mbps
  (DoT notification of 25 Jan 2023; Dec 2023 onwards). Broadband/narrowband splits are not
  comparable across these changes; totals are.
- **State/UT figures exist only from Dec 2021.** Earlier reports give internet subscribers by
  telecom *service area* (22 circles: Mumbai and Kolkata separate, North East together, UP split
  East/West, Bihar incl. Jharkhand, MP incl. Chhattisgarh, etc.), not by State.
- **Dec 2021 State split is unreliable for Chhattisgarh (2.17 mn) and Jharkhand (4.22 mn).**
  These were still largely booked under their parent circles (MP, Bihar); from Dec 2022 they
  look normal (15.6 and 17.4 mn). Similar, smaller shifts affect Arunachal Pradesh (4.9 mn in
  2021 vs 0.8 mn in 2022), Goa and the North East. Treat 2021 State values with caution.
- **Rural/urban per-100** depends on TRAI's rural/urban population estimates and the circle in
  which a SIM is registered; values above 100 or rural > urban (Kerala, Goa) are TRAI's.
