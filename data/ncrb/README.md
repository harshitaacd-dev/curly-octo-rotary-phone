# NCRB Crime in India: crimes against women and cyber crimes, 2012–2024

Downloaded from https://www.ncrb.gov.in (Crime in India, English edition) by
`scripts/ncrb_download.py`. `catalog.csv` lists every file with its year,
chapter, title and source URL.

These are **published aggregate tables** (national / state-UT / city /
district counts), not unit-level records; NCRB does not release FIR-level
microdata. Crime in India 2025 had not been published as of October 2026.

Layout: `<year>/women/` and `<year>/cyber/`. Tables tagged with both topics
(e.g. cyber crimes against women) sit in the folder of the first match.

## District-wise files
- Crimes against women: every year. 2012 and 2013 are PDFs that each cover
  2001 to that year. From 2014 onward the files are Excel.
- Cyber crimes: 2017–2024 (Excel). NCRB did not publish these by district
  before 2017.

## Caveats
- 2012–2016 tables are mostly PDF; Excel is generally available from 2017.
  Where an Excel link on the NCRB site was broken, the PDF was saved instead.
- Crime heads change over time: the 2014 reclassification of crimes against
  women, and the move from IPC to BNS from 1 July 2024 (2024 tables combine
  both codes). Check column definitions before you build a panel.
- Re-run to refresh or extend: `python scripts/ncrb_download.py 2012 2025 data/ncrb`
  (existing files are skipped).
