# Part C: Telegram image-based sexual abuse groups (India), 2014–2026

Measures how morphed and other non-consensual intimate media have grown on Indian
Telegram groups since 2014. The aim is to show what NCRB's registered cases miss, since
most cases go unreported. The method follows AI Forensics, *Harassment As Infrastructure*
(2026; Italy and Spain). Its practice categories (Table 3), link typology (Table 1),
bots (3.6) and archives/monetisation (3.6) are reproduced here. The languages are those
of the threat corpus on the `text_threats` branch: Hindi, Hinglish, Bangla, Meitei,
Indian English and Tamil.

## Ethics and retention (as approved)
- **Retention ends 19 Nov 2026** (submission). After that date `tg_collect.py` and
  `tg_analyse.py` refuse to run. `python scripts/tg_purge.py data/telegram telegram_chats.json`
  deletes everything (collection, search terms, candidates, outputs and session); also log the research account out of all devices.
- **Media is never downloaded.** Only the type, size and a hashed file id are kept.
- **Everything is pseudonymised before it is written** (`scripts/tg_privacy.py`):

| Item | Stored as |
|---|---|
| Senders, forwarded-from accounts and chats, admin signatures, forwarded-from names | salted hash |
| Chat titles and @usernames | salted hash (renames are still detected) |
| Phone numbers, emails, UPI IDs, Aadhaar-style numbers, personal @mentions in text | `[PHONE #…]`, `[EMAIL #…]`, `[UPI #…]`, `[ID #…]`, `[USER #…]` |
| Non-Telegram links (e.g. a victim's Instagram) | domain plus hashed path: `[URL instagram.com #…]` |
| Telegram links (`t.me/…`) | **in clear**, approved for finding further groups. Listed in `snowball_leads.csv` |
| Bot usernames (`@…bot`, via-bot, bot senders) | **in clear**: tools, not people; needed to measure nudify bots |
| Message text | kept with the replacements above. **Personal names written in free text are not caught**; they go when the text column is deleted |
| Telethon login session | login only; its cache of user ids, usernames, names and phone numbers is switched off |

Raw data, the session and the chat list are git-ignored. Never commit anything from
`data/telegram/`.

## Setup (on your own computer)
1. `pip install telethon` (plus `cryptg` for speed).
2. Use a dedicated research account. In its Telegram app settings, turn off **automatic
   media download** for every network type.
3. Join each group or channel by hand, then list it in `telegram_chats.json`. `cohort` is
   your grouping, e.g. by main language:
   ```json
   {"chats": [{"alias": "HI-01", "cohort": "hindi", "chat": "https://t.me/+AbCdEf"},
              {"alias": "TA-01", "cohort": "tamil", "chat": "-1001234567890"}]}
   ```
4. Set `TG_API_ID` and `TG_API_HASH` (from my.telegram.org) and `TG_SALT` (a long random
   string kept in a password manager; every run must use the same one).

## Run
- **Collect:** `python scripts/tg_collect.py telegram_chats.json data/telegram`
  - The first run for a chat reads its **whole surviving history**, so messages are dated
    back to the oldest one Telegram still holds.
  - Later runs (e.g. daily) add new messages, re-snapshot edits and deletions from the
    last 7 days, and log each chat's status (`unavailable` once banned), creation date
    and oldest surviving message.
- **Analyse:** `python scripts/tg_analyse.py data/telegram data/telegram/out`
- **Check the keywords:** fill the `correct (1/0)` column of `validation_sample.csv` and
  report precision per practice. Add or fix patterns in `lexicon.csv`.
- **Code links:** put the `uncoded` domains from `domains.csv` into a `domain,category`
  CSV and rerun with `--codes`.
- **Snowball:** check `snowball_leads.csv` for new groups, join them by hand and add them
  to the chat list.

## Finding groups
`python scripts/tg_find.py data/telegram/search_terms.txt data/telegram --config telegram_chats.json`

- **What it does:** runs Telegram's own public search with the research account. It
  matches group, channel and bot names. Only metadata is read (title, @username,
  description, members, type, creation date), never messages or media. Accounts of people
  found by a search are dropped.
- **Search terms:** write them in `data/telegram/search_terms.txt`, one per line,
  optionally followed by a tab and a cohort. Build the list from `lexicon.csv`,
  news coverage and terms seen inside groups. The file lives in the data folder so it
  stays out of git (this repository is public) and is deleted with the purge.
- **Outputs:**
  - `candidates.csv` (git-ignored): one row per chat or bot, with the terms that found it
    and whether it is already in your chat list. Fill in the `decision` column as you
    screen; it is kept on re-runs.
  - `search_log.csv`: when each term was searched and what came back, for your methods
    section.
- **Limits:** only public chats can be found, by name, and Telegram caps results per term.
  Private groups come from snowballing (`snowball_leads.csv`).
- **Screening:** `python scripts/tg_screen.py data/telegram/candidates.csv` shows one
  candidate at a time with a keyword-based suggestion; press a key to decide (a note can
  follow the key). Decisions, cohort, note and time are saved straight away. Then
  `python scripts/tg_screen.py data/telegram/candidates.csv --build telegram_chats.json`
  adds the included chats to the chat list with aliases (HI-01, TA-01, …).
- **Joining is by hand:** never pay, and never share invite links to get into a group.

## Measuring morphed media without seeing it
A message counts as morphed media (`morph = 1` in `messages_coded.csv`; `morph_*` in
`monthly.csv`) when any of these holds:
1. **Text:** it matches the `deepfake` practice, e.g. *morph*, *deepfake*, *face swap*,
   *nudify*, *edit karke*, *kapde utaar*, *nangi photo bana*, मॉर्फ, डीपफेक, মর্ফ, மார்ஃப்.
2. **Nudify bot:** it was sent by, sent through, or mentions or links a bot whose name
   looks like a nudify, undress or face-swap tool (`bots.csv`).
3. **AI generator link:** it links to a site in the report's "NCII AI Image & Video
   Generator" category.

`morph_by_text`, `morph_by_nudify_bot` and `morph_by_ai_generator_link` keep the three
signals apart.

## The time series and its limits
`monthly.csv` has one row per month for all chats (`dimension = all`), per cohort and
per detected language. The columns are messages, active and new senders, media,
forwards, morphed-media messages and senders, and one count per practice.
`chats_observable` is how many chats existed in the data by that month.

Read it with these limits in mind:
- **Survivorship.** Only groups that still exist can be read, and admins and Telegram
  delete content. Early years are thin because their groups are gone, not necessarily
  because there was less abuse. Report rates per observable chat as well as counts.
- **Telegram's own growth.** Telegram's Indian user base grew sharply (notably in 2021),
  so rising counts partly reflect the platform.
- **Moderation changes.** Telegram's takedowns rose after August 2024.
- **Forwards** carry the date the content was first posted (`fwd_date` in
  `messages_coded.csv`). Use it to date old content resurfacing in newer groups.
- **Keywords** are drafts. Bangla, Tamil and the Romanised forms of both need a
  native-speaker check. **Meitei has no terms yet**: Meitei messages are only caught
  through English or Hinglish words, bots and links.

## Outputs (`data/telegram/out/`, local only)
| File | Report section |
|---|---|
| `monthly.csv` | the time series |
| `messages_coded.csv` | per-message coding without text (Table 3 practices, 3.3 roles) |
| `chat_summary.csv` | Table 2: scale per chat; also creation date, bans, renames |
| `cohort_overlap.csv`, `chat_overlap.csv` | 3.1.1–3.1.3: shared senders and media |
| `links.csv`, `domains.csv` | Table 1: external platforms |
| `bots.csv` | 3.6: automation, nudify bots |
| `payments.csv` | 3.6: monetisation (UPI in place of PayPal/Bizum) |
| `snowball_leads.csv` | finding further groups |
| `validation_sample.csv` | keyword precision |
| `gephi_nodes.csv`, `gephi_edges.csv` | Fig. 27-style sender–chat network |

## Encountering child sexual abuse material
Viewing it is an offence under IT Act s.67B, and POCSO s.15 requires reporting it.
Messages matching `csam_marker` are flagged from text alone. Do not open, screenshot or
forward their media. Note the chat alias and message id and report through
cybercrime.gov.in ("Report Women/Child Related Crime"), as in the ethics protocol.
