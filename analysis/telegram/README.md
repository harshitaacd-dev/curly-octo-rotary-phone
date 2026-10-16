# Part C: Telegram image-based sexual abuse groups (India)

Collection and analysis tools for an India study modelled on AI Forensics, *Harassment As
Infrastructure* (2026), which covered Italy and Spain. Cohorts (e.g. Hindi/Hinglish vs Tamil)
take the place of that report's two countries.

**Never committed:** `data/telegram/` (messages, login session, state), the chat list
(`telegram_chats*.json`) and anything derived from message text or URLs. All are in
`.gitignore`. Only aggregate tables with no names, links or text should be copied here.

## Setup
- `pip install telethon` (plus `cryptg` for speed).
- Use a dedicated research account. In its Telegram app settings, turn off **automatic media
  download** on every network type, so joining a group does not save images to the device.
- Join each group or channel by hand, then list it in `telegram_chats.json`:
  ```json
  {"chats": [{"alias": "HI-01", "cohort": "hindi", "chat": "https://t.me/+AbCdEf"},
             {"alias": "TA-01", "cohort": "tamil", "chat": "-1001234567890"}]}
  ```
- Set `TG_API_ID`, `TG_API_HASH` (my.telegram.org) and `TG_SALT` (a long random string; keep
  it in a password manager, as every run must use the same one).

## Run
- **Collect** (repeat daily or so, e.g. from cron, for the whole observation period):
  `python scripts/tg_collect.py telegram_chats.json data/telegram`
  Each run adds new messages, re-snapshots messages from the last 7 days that were edited
  (`--revisit-days`), marks those deleted, and logs each chat's title, size and status
  (`unavailable` once Telegram bans it).
- **Analyse:** `python scripts/tg_analyse.py data/telegram data/telegram/out`
  Code the `uncoded` rows of `domains.csv` by hand into a `domain,category` CSV and rerun
  with `--codes`. Open `gephi_nodes.csv` / `gephi_edges.csv` in Gephi (Data Laboratory →
  Import Spreadsheet).

## What is kept
| Item | Stored as |
|---|---|
| Users, bots, forwarded-from chats | salted HMAC (16 hex chars) |
| Media | type, MIME, size, hashed Telegram file id. **The file is never fetched.** |
| Text, hidden links, button links | as is (needed for coding); local only |
| UPI IDs and payment links (`payments.csv`) | salted hash only |

A media key matches when a file is forwarded or re-sent, not when the same image is
uploaded again, so cross-chat media overlap is a lower bound, like the report's
hash-based 8%.

## Mapping to the report
| Report | Here |
|---|---|
| Active senders, messages, media files (Table 2) | `chat_summary.csv` |
| Shared senders, links and media across countries (3.1.1–3.1.3) | `cohort_overlap.csv`, `chat_overlap.csv`, `domains.csv` |
| External platform typology (Table 1) | `links.csv` / `domains.csv` categories |
| Monetisation (3.6): PayPal, crypto, Bizum | `payments.csv`: UPI IDs, `upi://` links, Razorpay/Instamojo/Cosmofeed pages |
| Groups closed and reopened under the same name | `chats.jsonl` status and title over time |

## Encountering CSAM
Viewing child sexual abuse material is an offence under IT Act s.67B, and POCSO s.15 requires
reporting it. Do not open, screenshot or forward it. Note the chat alias and message id and
follow the reporting route in the approved ethics protocol (cybercrime.gov.in, "Report
Women/Child Related Crime").
