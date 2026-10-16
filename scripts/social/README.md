# Collecting new comments: Reddit, YouTube, Telegram

These scripts collect fresh comments for threat and misogyny text mining. They write in a common format, so the output can be scored against the labelled corpus in `data/text_threats/`.

| Platform | Script | Account / key needed | What you get |
|---|---|---|---|
| Reddit | `reddit_comments.py` | **None** with the default Arctic Shift backend. The official API needs a Reddit "script" app. | Comments matching keywords in chosen subreddits, or full comment trees under matching posts |
| YouTube | `youtube_comments.py` | `YOUTUBE_API_KEY` (free; Google Cloud → YouTube Data API v3) | All top-level comments and replies on videos found by search, channel or video ID |
| Telegram | `telegram_comments.py` | **None** for `--web` (channel posts only). For comments: `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` from my.telegram.org, plus `pip install telethon` | Channel posts, the comments under them, and public group messages |

### AI content and deepfakes (2018–2024)

| Script | Key needed | What it does |
|---|---|---|
| `factcheck_deepfakes.py` | **None** by default (WordPress search of Alt News, Factly, Newschecker, Fact Crescendo, DFRAC); optional Google Fact Check Tools API | Fact-checks of deepfakes, AI-generated and manipulated media, with the YouTube videos each one links. Writes `data/deepfakes/factchecks_2018_2024.csv` and `factcheck_youtube_seeds_2018_2024.csv`. Each video's status (available / removed) is checked with YouTube's public oEmbed endpoint. **Most linked videos that are still up are the authentic original or the fact-checker's own explainer, not the fake** (see `link_role`); the fakes themselves mostly circulated on X, Facebook or WhatsApp, or were removed. |
| `youtube_discover.py --mode ai-channels` | `YOUTUBE_API_KEY` | Searches AI-content queries one year at a time and outputs channels with their evidence: creator self-label (`containsSyntheticMedia`), AI wording in titles/descriptions/tags, declared country, and (with `--profile-channels`) the share of recent uploads that are AI-worded. Fill in the `manually_verified` column by hand. |
| `youtube_discover.py --mode deepfakes` | `YOUTUBE_API_KEY` | The same, for deepfake / "fake video" queries; with `--comments N` it also counts debunking comments ("fake hai", "AI hai", "edited"). |
| `youtube_comments.py --seed-file ...` | `YOUTUBE_API_KEY` | Collects the comments under seed videos: `seeds/comma_youtube_videos.csv` (the 150 videos ComMA annotated, 77 with sexual-threat comments) or the fact-check seed file. |

Videos are **never downloaded**; only metadata and comments are collected. The discovery and fact-check outputs (public metadata, no comment text or usernames) can be committed. Comment pulls go to the git-ignored `data/social_raw/`.

Default subreddits, keywords and search queries are in `targets.json`. Edit that file, or override any of them on the command line.

```bash
# Reddit: keyword hits, Jan-Jun 2025, 30-day search windows
python scripts/social/reddit_comments.py --mode keywords --after 2025-01-01 --before 2025-07-01

# Reddit: whole threads under posts whose title matches a query
python scripts/social/reddit_comments.py --mode threads --subreddits india TwoXIndia \
    --queries "woman journalist" "marital rape" --after 2025-01-01 --max-threads 30

# Deepfake fact-checks 2018-2024 (no key)
python scripts/social/factcheck_deepfakes.py --from 2018-01-01 --to 2024-12-31

# YouTube (10k quota units/day: one search costs 100, one page of 100 comments costs 1)
python scripts/social/youtube_discover.py --mode ai-channels --profile-channels 100   # ~7.5k units
python scripts/social/youtube_discover.py --mode deepfakes --comments 100            # next day
python scripts/social/youtube_comments.py --queries --seed-file scripts/social/seeds/comma_youtube_videos.csv
export YOUTUBE_API_KEY=...
python scripts/social/youtube_comments.py --after 2025-01-01 --videos-per-query 20
python scripts/social/youtube_comments.py --queries --video-ids VIDEOID1 VIDEOID2

# Telegram
python scripts/social/telegram_comments.py --web --channels <public_channel>
export TELEGRAM_API_ID=... TELEGRAM_API_HASH=...
python scripts/social/telegram_comments.py --channels <public_channel> --after 2025-01-01
```

## Output

Each run writes `data/social_raw/<platform>/<platform>_<tag>_<UTC timestamp>.csv.gz` with these columns:

`platform, collected_at, target, item_id, parent_id, thread_id, thread_title, community, created_at, author_hash, text, score, url, rape_lexicon, hinglish_threat_lexicon, hinglish`

- **`author_hash`** is an HMAC-SHA256 pseudonym; usernames are never stored. The key comes from `SOCIAL_HASH_SALT`, or a random salt saved in `data/social_raw/.salt`. Keep that salt private and don't change it, so the same author keeps the same pseudonym across runs.
- **Keyword flags.** `rape_lexicon`, `hinglish_threat_lexicon` and `hinglish` use the same regexes as `build_threat_corpus.py`. They are flags for finding candidates, **not labels**.
- **`data/social_raw/` is git-ignored on purpose.** It contains identifiable people's comments, so keep it on encrypted or institutional storage, not in a public repository.

## Platform notes

- **Reddit / Arctic Shift.**
  - It is a third-party archive of public Reddit data, built for research.
  - It records comments shortly after they are posted, so very recent threads are incomplete. Prefer date ranges that are at least a few weeks old.
  - Edits after it captured a comment are missed, and deleted comments may still be present. Before publishing, drop anything that has since been deleted on Reddit.
  - Full-text search is run in `--window-days` chunks, because long ranges time out on the server.
  - The `official` backend uses Reddit's own API. It can't search comment text, so it supports `--mode threads` only. Reddit blocks this cloud machine, so that backend has not been tested here.
- **YouTube.**
  - Comments that are disabled, held for review or removed are not returned.
  - Search results are ranked by relevance, not sampled at random. Record the queries you used with your results.
- **Telegram.**
  - Only collect from public channels and groups. Joining private groups to collect data raises serious ethics and consent issues.
  - The web preview shows posts only. Comments live in each channel's linked discussion group and need the Telethon mode.
  - Telethon could not be installed in this cloud environment, so that mode has not been run here. The web mode was tested.

## Ethics checklist

- Get IRB / ethics-committee approval before collecting at scale.
- Collect only what you need, store it securely, and set a deletion date.
- Never publish verbatim threats or usernames; quotes can be searched back to the victim. Paraphrase them, or publish only IDs and labels.
- Follow each platform's terms (the Reddit Data API terms, YouTube API Services terms, Telegram terms). These scripts are rate-limited; don't remove the sleeps.
- If you find content showing imminent danger or child sexual abuse material, follow your institution's reporting protocol. Don't download media.
