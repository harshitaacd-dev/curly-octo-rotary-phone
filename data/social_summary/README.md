# Comment-collection summaries (counts only)

Aggregates of `youtube_comments.py` seed runs, built with
`scripts/social/summarise_youtube.py`. They contain **no comment text and no usernames**;
the comments themselves stay in the git-ignored `data/social_raw/`.

| File | Contents |
|---|---|
| `youtube_<tag>_per_video.csv` | One row per seed video: `available` (1 = returned by `videos.list`), `comments_status` (`ok`, `disabled_or_error`, `video_unavailable`, `not_collected_quota`), comments collected (`top_level` = not replies) and keyword-flag counts |
| `youtube_<tag>_by_group.csv` | The same counts summed overall and by each grouping column |

Runs on 2026-10-16: `comma_seeds` (`--max-comments 2000`, ComMA's 150 annotated videos,
grouped by whether ComMA annotators found any sexual threat) and `factcheck_seeds`
(`--max-comments 1000`, the 565 videos in `data/deepfakes/factcheck_youtube_seeds_2018_2024.csv`,
grouped by `kind`, `mentions_woman` and `link_role`).

- A video linked from several fact-checks counts in **every** group it belongs to, so group rows can add up to more than the "all" row.
- The per-video comment cap is checked once per page of 100, so a video can go slightly over it.
- `rape_lexicon`, `hinglish_threat_lexicon` and `hinglish` are keyword flags for finding candidates, **not labels**.
