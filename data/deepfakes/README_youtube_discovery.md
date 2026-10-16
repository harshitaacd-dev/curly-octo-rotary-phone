# YouTube discovery outputs (metadata only)

Built by `scripts/social/youtube_discover.py`. No videos, thumbnails, comment text or usernames.

## `youtube_ai-channels_2018_2024_*` (run 2026-10-16, ~7,200 quota units)

10 AI-content queries x 7 years x 1 search page (50 videos), `regionCode=IN`, ranked by relevance
(not a random sample): 3,068 videos, 2,047 channels, 1,189 of which declare country = IN
(462 declare none). The 100 top AI-worded channels in India or with no country set were profiled
on their last 50 uploads.

- `ai_cue` / `ai_cue_terms`: AI wording in title, description (first 2,000 characters) or tags.
  **Rescored after the run**: the first regex matched "udio" inside "audio", Hindi "suno"
  (listen), "runway" and hashtags such as #airpods / #aids. The original flag is kept as
  `ai_cue_regex_v1` (videos) and `n_ai_cue_regex_v1` (channels). For udio / suno / runway only
  title matches are kept, since descriptions and tags were not stored.
- `recent_ai_share` (channels) still uses the **old regex** and may overcount; recompute on the
  next profiling run.
- `self_labelled` (`status.containsSyntheticMedia`) was **never returned**, for any of the 3,068 videos.
- Plain "ai" still matches non-AI uses (Hindi romanisation such as "swar ai", the TV serial
  "Janani AI Ki Kahani"). Fill in `manually_verified` before using channel lists as evidence.
