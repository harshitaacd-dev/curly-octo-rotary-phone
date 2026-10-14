# NCRB Crime in India tables, 2012–2024

Downloaded from https://www.ncrb.gov.in (Crime in India, English edition) by
`scripts/ncrb_download.py`. `catalog.csv` lists every file with its year,
chapter, title and source URL.

These are **published aggregate tables** (national / state-UT / city /
district counts), not unit-level records; NCRB does not release FIR-level
microdata. Crime in India 2025 had not been published as of October 2026.

Topics: crimes against women, cyber crimes, human trafficking, sexual
offences, crimes against children and missing persons.

Layout: `<year>/<topic>/`. A table that matches more than one topic (e.g. cyber
crimes against women) sits in the folder of the first match, in the order
women, cyber, trafficking, sexual, children, missing.

Cleaned State/UT datasets built from these files are in `data/clean/`.

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
- Two NCRB links serve the wrong year: the 2019 Table 3A.2 Excel is the 2020
  file, and the 2012 cyber Tables 18.6/18.7 are the 2013 files.
  `scripts/build_state_datasets.py` checks each table's own title and works
  around both; the 2019 Table 3A.2 PDF (`2019/women/Table-3A.2_2.pdf`) was
  downloaded separately for this and is not listed in catalog.csv.
- Re-run to refresh or extend: `python scripts/ncrb_download.py 2012 2025 data/ncrb`
  (existing files are skipped).

## Chapter PDFs
`chapters/<year>/` holds the narrative cyber-crime and crime-against-women chapters for
2012–2015, downloaded while looking for State-level 2015 cyber crime heads. They contain
only all-India tables. The "2012" cyber chapter on NCRB's site is the 2013 one.
