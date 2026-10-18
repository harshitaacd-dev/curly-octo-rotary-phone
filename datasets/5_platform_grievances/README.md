# Datasets

One CSV per platform, extracted from the archived reports in [`../reports/`](../reports/). All the files share one long layout ("tidy" data): **one row per number published**. That makes it easy to filter, pivot or chart in a spreadsheet, pandas, R and similar tools.

| File | Platform | Rows | Periods | What's in it |
|---|---|---|---|---|
| `google.csv` | Google (YouTube and other products) | 1,358 | Apr 2021 – Aug 2026 (65) | user complaints and removal actions by reason; removals from automated detection |
| `meta.csv` | Facebook, Instagram, Threads | 6,350 | May 2021 – Aug 2026 (63) | content actioned and proactive rate by policy area; grievances by category (received, tools provided, specialised review, actioned); GAC orders |
| `whatsapp.csv` | WhatsApp | 901 | May 2021 – Aug 2026 (63) | grievances by topic (received, accounts actioned); accounts banned, incl. proactively; GAC orders |
| `x.csv` | X (Twitter) | 1,609 | May 2021 – Feb 2026 (57) | grievances and URLs actioned by issue type (to Sep 2025), then reports and valid reports actioned with % breakdowns; suspension appeals; global proactive suspensions |
| `snap.csv` | Snapchat | 3,939 | Jun 2021 – Sep 2026 (64) | reports, enforcements and unique accounts enforced by reason; split from Dec 2024 into all / reported / proactive; median turnaround times; CSAM/CSEA account deletions |
| `sharechat.csv` | ShareChat | 878 | Jun 2021 – Oct 2022 (17) | law enforcement requests; user reports by reason (count and/or % share); takedowns; account bans by type and duration |
| `moj.csv` | Moj | 757 | Jun 2021 – Oct 2022 (17) | same as ShareChat |
| `pinterest.csv` | Pinterest | 4,600 | Jun 2024 – Aug 2026 (27) | actions on reported content and voluntary actions, by policy and surface (Pins, Boards, Accounts, Comments) |
| `roblox.csv` | Roblox | 247 | May–Jun 2025, May–Jul 2026 (5) | grievance reports and enforcement actions by category; global proactive moderation total |
| `india_it_rules_reports.xlsx` | all | | **everything in one Excel workbook**: headline monthly totals (SUMIFS formulas), all data in one filterable sheet, one sheet per platform, validation and report index. Rebuild with `python3 scripts/build_workbook.py`. |
| `validation.csv` | all | 707 | | every published total compared with the sum of its categories (see below) |

## Columns

| Column | Meaning |
|---|---|
| `platform` | Company or app that published the report |
| `service` | Product the number refers to: Facebook/Instagram/Threads for Meta, Pins/Boards/Accounts/Comments for Pinterest. `All` = not product-specific (e.g. Meta's GAC orders). `(global)` marks figures the platform says are worldwide, not India-only. |
| `period_start`, `period_end` | Reporting period covered (ISO dates), as stated in the report. For X, this follows X's monthly cadence where the PDF misstates it; see `../reports/index.csv`. |
| `section` | Part of the report the number comes from, e.g. `user grievances`, `proactive enforcement`, `accounts banned`, `GAC orders` |
| `category` | Reason, policy area or topic as the platform names it. **`All` = the platform's own total** for that section and metric. |
| `metric` | What is counted, using the platform's own terms (e.g. `reports received`, `removal actions`, `content actioned`, `accounts banned`) |
| `value` | The number |
| `unit` | `count`, `percent`, `minutes (median)`, or `count (rounded in source)`. That last one marks values printed abbreviated, such as 676.4K, 1.8 M, 10.7L (lakh) or 1.2Cr (crore), and expanded here, so they are approximate. |
| `notes` | Any correction or interpretation applied to the value |
| `source_file` | The archived report the row came from |

Example: Instagram's reports received for hacked accounts in March 2024:

```
platform,service,period_start,period_end,section,category,metric,value,unit,notes,source_file
Meta,Instagram,2024-03-01,2024-03-31,user grievances,Account has been hacked,reports received,396,count,,reports/meta/meta_india_2024-03.pdf
```

## Things to know before analysing

- **Don't compare raw numbers across platforms.** Each platform counts something different, and the `metric` names keep the platform's own wording on purpose:
  - Google counts removal *actions* on URLs.
  - Meta counts *pieces of content* actioned.
  - WhatsApp counts *accounts* banned.
  - X counts *URLs* actioned.
  - Snapchat counts *enforcements* and *unique accounts*.
- **Category names change over time.** Platforms rename and regroup categories (e.g. Meta's "Terrorist Propaganda" became "Terrorism"; Roblox revised its whole list in 2026). Names are kept as published, with only spelling and capitalisation variants merged.
- **Global vs. India.** X's proactive suspensions and Roblox's proactive moderation are worldwide figures, as both platforms state. They are labelled `(global)` in `service` and `section`.
- **Meta's content-actioned figures are rounded** in the source (unit `count (rounded in source)`). Values below 1,000 are printed in full. Meta's proactive rate is a percentage.
- **Unique-account counts overlap.** Snapchat's per-reason "unique accounts enforced" add up to more than the total, because one account can be enforced for several reasons.
- **Blank vs. zero.** "Nil" and "None" in the source are stored as 0. Cells shown as "-", "N/A", "Not Available" or "<1" are left out, because no single number was published.
- **Early ShareChat/Moj months** (to Apr 2022) give only the % share of user reports by reason, not counts.
- **WhatsApp's proactive bans** are a subset of total bans (metric `accounts banned proactively (before any user report)`), not an extra category.

## Validation

`validation.csv` compares every published total (`category = All`) with the sum of the categories listed under it. Two other checks were also run:

- every exact value in the datasets was found in the text of its source document
- spot checks against the PDFs

In 632 of 707 cases the categories add up exactly. The 75 that don't were each checked against the source. **They are discrepancies in the platforms' own reports, not extraction errors.** The datasets keep the numbers as published:

- **Meta, Instagram grievance tables (Sep 2023 – Jul 2025):** one category is consistently left out of the published table, so the rows sum 600–1,400 short of the stated total.
- **Meta, other cases:**
  - Nov 2023 Facebook prints 5,311 for two different categories.
  - Feb 2026 Facebook prints "2,1409" for fake profiles.
  - Jul–Aug 2026 are slightly off; Meta notes a technical issue with the per-category numbers.
- **Snapchat:**
  - From Dec 2025, category rows sum a few units (1–14) below the totals.
  - Jun 2021 is short by a small amount.
  - Oct 2021 – Feb 2022 pages give only totals, or label the total and the categories differently.
  - Sep 2022 prints "1.644" for Hate Speech reports; it is stored as 1,644 (see `notes`).
- **Roblox:** May 2025 categories sum to 529 against a stated total of 519. Jun 2025 is off by 1.
- **Google:** Jul 2023 complaint reasons sum to 29,189 against a total of 29,190.

Percentage breakdowns aren't in the validation file. They add up to about 100% in every month except ShareChat and Moj in Nov 2021, whose pages omit the largest categories.

## Rebuilding

```bash
python3 scripts/extract/run_all.py
```

This needs `pdftotext` (poppler-utils). There is one extractor per platform in [`../scripts/extract/`](../scripts/extract/), and each one's docstring describes the report layouts it handles. Extraction is deterministic, so new months are picked up after running the download scripts and `scripts/build_index.py`.
