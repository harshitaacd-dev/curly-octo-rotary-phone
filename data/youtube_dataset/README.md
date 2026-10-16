# YouTube dataset: AI content, deepfakes and sexualised AI imagery (India, 2018–2024)

Built by `python scripts/social/build_youtube_dataset.py` from the committed discovery, seed
and summary files. **Metadata and counts only**: no comment text, no usernames, no media.
`youtube_dataset.xlsx` holds the same three tables plus this README.

## Sources (`source` column; a video can have several)

| Source | How videos were chosen | Videos |
|---|---|---:|
| `discovery:ai-channels_2018_2024` | 10 AI-content queries × 7 years, top 50 by relevance, regionCode=IN | 3,068 |
| `discovery:deepfakes_2018_2024` | 10 deepfake / fake-video queries × 7 years | 2,955 |
| `discovery:ai-channels_2022_2024_targeted` | 6 queries for sexualised AI imagery of Indian women × 2022–2024 | 820 |
| `seed:factcheck` | YouTube videos linked from Indian fact-checks of AI / deepfake / morphed media | 565 |
| `seed:comma` | Videos whose comments ComMA annotated for sexual threats | 150 |

Search results are ranked by relevance, not sampled: they show what YouTube surfaces for a
query, not prevalence. Seeds are selected on the outcome (fake or threat), so keep them
apart from discovery videos in any comparison.

## `videos.csv` — one row per video (7,440)

| Column | Meaning |
|---|---|
| `published_at`, `year`, `title`, `channel_*`, `views`, `comments`, `subscribers`, `language` | YouTube API metadata at collection (2026-10-16). `api_metadata` = 0 for 99 seed videos no longer available (title from oEmbed / fact-check) |
| `country`, `channel_in_india` | Channel's self-declared country (often blank) |
| `self_labelled` | `status.containsSyntheticMedia`; **never returned** for any video |
| `ai_cue`, `ai_cue_terms` | AI-tool / AI-content wording in title, description or tags (`AI_CUE` in `youtube_discover.py`, fixed version) |
| `sexual_title_flag` | Broad title flag, including generic "AI model / AI influencer" wording |
| `explicit_title_flag` | Narrower: explicitly sexualised title wording (hot, sexy, nude, MMS, bhabhi, 18+, see-through, अश्लील …) |
| `news_framing_flag` | Title reads as news / police / awareness (reporting on harm rather than the content) |
| `debunk_comments`, `comments_scanned`, `debunk_share` | Deepfakes run only: first ≤100 comments matching "fake hai / AI hai / edited …". Noisy — any "fake" counts |
| `factcheck_*`, `oembed_status` | Fact-check seeds: kind (ai-generated, ai-voice, deepfake/face-swap, edited/morphed), whether the article mentions a woman, publishers, first fact-check date, link role |
| `comma_*` | ComMA seeds: comments annotated and sexual-threat comments in ComMA |
| `seed_available`, `seed_comments_status`, `collected_*` | Seeds only: our comment collection (cap 2,000 ComMA / 1,000 fact-check per video) and keyword-flag counts (`rape_lexicon`, `hinglish_threat_lexicon`, `hinglish`) |

## `channels.csv` — one row per channel (5,027)

Counts of found / AI-worded / sexual / explicit videos, declared country, subscribers,
creation date, and `recent_ai_share` (share of the last 50 uploads with AI wording; from the
targeted run where available, otherwise the first AI-channels run, which used the older,
over-matching regex). `manually_verified` is blank: fill in by hand.

## `panel_year.csv` — year × source, 2018–2024

`all_discovery` rows pool the three discovery runs; other rows are per source. Counts of
videos, Indian channels, AI-worded, sexual / explicit titles, explicit-and-AI (also from
Indian channels), views, debunk comments.

## Caveats

- All flags are **keyword pointers for manual review, not labels**. Plain "ai" also matches
  Hindi romanisation; "fake" in comments matches "fake friends".
- Views and subscribers are as of collection, not as of publication.
- Explicit titles were not opened. Some may concern non-consensual imagery of real women;
  review only under an approved ethics protocol.
