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

## `youtube_deepfakes_2018_2024_*` (run 2026-10-16, ~10,060 quota units)

10 deepfake / fake-video queries x 7 years x 1 search page, `regionCode=IN`: 2,955 videos,
2,264 channels (975 declare IN, 581 none). The AI-cue regex is the fixed one.

- `debunk_comments` / `comments_scanned`: comments among the first 100 (by relevance) matching
  `DEBUNK` ("fake hai", "AI hai", "edited", "nakli", ...). 2,177 videos had comments scanned.
  **Noisy:** any comment containing "fake" counts, so off-topic videos ("fake friends",
  "fake blood", "fake number") rank high. Use it only together with `ai_cue` or manual review.
- Queries such as "fake viral video sach" and "morphed video viral" pull in many videos that are
  not about synthetic media.

## `sexual_title_flag` (both video files)

Title-keyword flag (hot, sexy, nude, MMS, obscene / अश्लील, bikini, AI girl / model / beauty,
sextortion, ...), added 2026-10-16. A **pointer for manual review, not a label**: it mixes news
about sextortion and morphed images, "MMS leak / viral video" clickbait naming real women,
celebrity deepfakes, explainers on nudify apps, and harmless matches (food "hot dog", "kiss").
Deepfakes run: 97 videos (53 from channels declaring India). AI-channels run: 11.
Nothing was viewed or downloaded; do not open flagged videos without an approved protocol.

## `youtube_ai-channels_2022_2024_targeted_*` (run 2026-10-16, ~1,880 quota units)

Targeted queries for sexualised AI imagery of Indian women: "AI saree model", "AI bhabhi",
"AI lookbook", "AI girl Indian", "AI influencer India", "AI model Indian beauty", 2022–2024,
one search page each: 820 videos, 680 channels (312 declare IN, 203 none). Top 50 AI-worded
channels profiled with the fixed regex (`recent_ai_share` is reliable here).

- `sexual_title_flag`: broad flag (includes generic "AI model / AI influencer" wording).
- `explicit_title_flag`: narrower — explicitly sexualised title wording (hot, sexy, bhabhi,
  nude, 18+, see-through, wet saree, cleavage, अश्लील, ...). 78 videos; 31 of them also carry
  AI wording (13 from channels declaring India). Most "AI bhabhi" results are not AI at all.
- Channels file adds `expl` / `sexf`: per-channel counts of the two flags.
- Metadata only. Several channel names are themselves sexualised; review under an approved protocol.
