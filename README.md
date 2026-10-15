# India IT Rules compliance reports archive

An archive of the monthly compliance reports that large social media platforms publish in India. Each report says how many user complaints the platform received, what action it took, and how much content or how many accounts it removed proactively, broken down by reason.

The reports are required by **Rule 4(1)(d) of the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021**. The rule applies to *significant social media intermediaries*: platforms with 5 million or more registered users in India. Reporting began in mid-2021.

Everything here was downloaded from the platforms' own websites on 14–15 October 2026. **[`reports/index.csv`](reports/index.csv)** lists every file with the period it covers, its source and any caveats.

**Datasets:** the numbers from every report have been extracted into one CSV per platform in [`datasets/`](datasets/), about 20,000 rows in all, covering complaints, removals, proactive enforcement, account bans and GAC orders, by category and month. [`datasets/README.md`](datasets/README.md) explains the columns, the caveats, and the validation against each report's own totals.

## Coverage

| Platform | Folder | Reports | Periods covered | Format |
|---|---|---|---|---|
| Google (YouTube, Search, Play, etc.) | `reports/google/` | 65 | Apr 2021 – Aug 2026 | original PDF |
| Meta (Facebook, Instagram, Threads) | `reports/meta/` | 64 | 15 May 2021 – Aug 2026 | original PDF |
| WhatsApp | `reports/whatsapp/` | 63 | 15 May 2021 – Aug 2026 | original PDF |
| X (Twitter) | `reports/x/` | 57 | 26 May 2021 – 25 Feb 2026 | original PDF |
| Snapchat | `reports/snap/` | 64 | Jun 2021 – Sep 2026 | web page snapshot |
| ShareChat | `reports/sharechat/` | 20 | Jun 2021 – Oct 2022, plus 2 earlier annual reports | web page snapshot |
| Moj | `reports/moj/` | 18 | Jun 2021 – Oct 2022 | web page snapshot |
| Pinterest | `reports/pinterest/` | 27 | Jun 2024 – Aug 2026 | web page snapshot |
| Roblox | `reports/roblox/` | 5 | May–Jun 2025, May–Jul 2026 | original PDF |
| **Total** | | **383** | | ≈75 MB |

Within each platform's range there are no missing months, except for Roblox.

"Web page snapshot" means the platform publishes the report as a web page, not a PDF. For these, the folder holds a PDF print of the page and a `.txt` copy of its text, and Pinterest also has an `.html` copy. Each `.txt` file starts with its source URL and the time it was retrieved.

## File naming

- **Google, Snapchat, ShareChat, Moj, Pinterest, Roblox:** `<platform>_india_YYYY-MM` = the month covered.
- **Meta:** `meta_india_YYYY-MM` follows the month label in Meta's download menu, which is *not* always the month covered (e.g. `2024-08` covers July 2024). The very first report has two parts (`2021-06_part1`, `_part2`). Use `index.csv` for the actual period.
- **WhatsApp:** `whatsapp_india_published_YYYY-MM-DD` = the publication date WhatsApp lists. Each report covers the previous month, roughly; see `index.csv`.
- **X:** original filenames, `India-ITR-<Month>-<Year>.pdf`, named after the publication month. The file for month M covers the 26th of M−2 to the 25th of M−1.

## Caveats

- **The numbers are not comparable across platforms.** Each company counts differently: content pieces vs. accounts, complaint categories, what "proactive" means, and so on. Reporting formats have also changed over time within each platform.
- **X's PDFs contain date errors.** Eight reports (Nov 2023, Mar–Jun 2025, Jan–Mar 2026) state the wrong period in their opening sentence: a wrong year, or text carried over from an earlier month. `index.csv` gives the period that matches the report's data sections and X's monthly cadence, and its `notes` column quotes what the PDF says.
- **X:** the most recent report on X's India page is the one published in March 2026. Nothing newer was listed when this archive was built.
- **ShareChat and Moj:** their help-centre archives stop at October 2022. No later reports were found there.
- **Roblox:** only five reports could be found. Its transparency page links to the latest two, and two 2025 files were found through search. The others may exist at addresses I couldn't find.
- **Meta and WhatsApp** serve their PDFs through expiring signed links. `index.csv` therefore records their index pages as the source, not the file URL.
- The period columns in `index.csv` were extracted automatically from each document and spot-checked. Treat the PDF itself as authoritative.

### Not included

Other platforms classed as significant social media intermediaries, such as **LinkedIn, Telegram and Koo** (Koo shut down in 2024), are not in this archive. I couldn't find a public monthly IT Rules report for them on their own sites. Some platforms report Indian figures only in their global transparency reports. Those are out of scope here.

## Updating

```bash
python3 scripts/build_index.py      # rebuild reports/index.csv (needs pdftotext + python-dateutil)
bash scripts/fetch_direct.sh        # new X, Google and Roblox reports (skips files already present)
python3 scripts/extract/run_all.py  # rebuild datasets/ from the reports
```

Meta, WhatsApp, Snapchat, ShareChat/Moj and Pinterest need a real browser. The Node scripts in `scripts/` use Playwright:

- `meta_list_links.js` selects each year and month in Meta's report menu and writes the download links to JSON. Download those promptly, because the links expire.
- `whatsapp_list_links.js` saves WhatsApp's report page, whose links point to the PDFs. These links expire as well.
- `snap_capture.js <outdir>` and `pinterest_capture.js <outdir>` save every month as PDF + text.
- `capture_pages.js <outdir> <list>` saves a list of pages (`<name> <url>` per line). It was used for ShareChat and Moj. Moj URLs need a trailing slash.

## Sources

- Google: <https://transparencyreport.google.com/> (files under `storage.googleapis.com/transparencyreport/report-downloads/`)
- Meta: <https://transparency.meta.com/reports/regulatory-transparency-reports/>
- WhatsApp: <https://www.whatsapp.com/legal/india-monthly-reports>
- X: <https://transparency.x.com/en/reports/countries/in>
- Snapchat: <https://values.snap.com/privacy/transparency/india-transparency-page>
- ShareChat: <https://help.sharechat.com/transparency-report/>
- Moj: <https://help.mojapp.in/transparency-report/>
- Pinterest: <https://policy.pinterest.com/en/india-transparency-report>
- Roblox: <https://about.roblox.com/transparency>

All reports remain the work of the respective companies. They are archived here for research and reference.
