"""Collect YouTube comments (top-level and replies) via the YouTube Data API v3.

Needs an API key: Google Cloud console -> enable "YouTube Data API v3" ->
Credentials -> API key, then `export YOUTUBE_API_KEY=...`.
Default quota is 10,000 units/day: a search call costs 100 units, a page of
100 comments costs 1 unit, so ~50 searches + ~5,000 comment pages per day.

Videos come from (any combination):
  --queries     search.list (regionCode/relevanceLanguage from targets.json)
  --video-ids   explicit video IDs
  --channel-ids every recent upload of a channel
  --seed-file   a CSV with a video_id column, e.g.
                scripts/social/seeds/comma_youtube_videos.csv (videos ComMA annotated)
                data/deepfakes/factcheck_youtube_seeds_2018_2024.csv (fact-checked fakes)

Examples:
  python scripts/social/youtube_comments.py --after 2025-01-01 --videos-per-query 20
  python scripts/social/youtube_comments.py --video-ids dQw4w9WgXcQ --max-comments 5000
"""
import argparse
import os
import sys

import pandas as pd
import requests

from common import OUT, get_json, iso, load_targets, new_session, now, pseudonym, save

API = "https://www.googleapis.com/youtube/v3"
COST = {"search": 100}  # every other read endpoint used here costs 1 unit
UNITS = {"used": 0}  # approximate units spent by this process


class QuotaExceeded(Exception):
    """The daily quota is spent: stop at once, save what we have, don't retry."""


def call(s, endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    UNITS["used"] += COST.get(endpoint, 1)
    try:
        return get_json(s, f"{API}/{endpoint}", params)
    except requests.HTTPError as e:
        if "quotaExceeded" in e.response.text or "dailyLimitExceeded" in e.response.text:
            raise QuotaExceeded(endpoint) from None
        raise


def search_videos(s, query, n, region, lang, after, before):
    vids, token = [], None
    while len(vids) < n:
        p = {"part": "snippet", "q": query, "type": "video", "maxResults": min(50, n - len(vids)),
             "order": "relevance", "regionCode": region, "relevanceLanguage": lang}
        if after:
            p["publishedAfter"] = iso(after).replace("+00:00", "Z")
        if before:
            p["publishedBefore"] = iso(before).replace("+00:00", "Z")
        if token:
            p["pageToken"] = token
        res = call(s, "search", **p)
        vids += [(i["id"]["videoId"], i["snippet"]["title"], i["snippet"]["channelTitle"])
                 for i in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break
    return vids


def channel_uploads(s, channel_id, n):
    ch = call(s, "channels", part="contentDetails", id=channel_id)
    playlist = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    vids, token = [], None
    while len(vids) < n:
        p = {"part": "snippet", "playlistId": playlist, "maxResults": 50}
        if token:
            p["pageToken"] = token
        res = call(s, "playlistItems", **p)
        vids += [(i["snippet"]["resourceId"]["videoId"], i["snippet"]["title"],
                  i["snippet"]["channelTitle"]) for i in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break
    return vids[:n]


def video_meta(s, ids):
    meta = {}
    for i in range(0, len(ids), 50):
        res = call(s, "videos", part="snippet", id=",".join(ids[i:i + 50]))
        meta.update({v["id"]: (v["snippet"]["title"], v["snippet"]["channelTitle"])
                     for v in res.get("items", [])})
    return meta


def comment_row(c, video_id, title, channel, target, parent=""):
    sn = c["snippet"]
    return {
        "platform": "youtube", "collected_at": now(), "target": target,
        "item_id": c["id"], "parent_id": parent or video_id, "thread_id": video_id,
        "thread_title": title, "community": channel, "created_at": sn.get("publishedAt"),
        "author_hash": pseudonym(sn.get("authorChannelId", {}).get("value")
                                 or sn.get("authorDisplayName")),
        "text": sn.get("textOriginal") or sn.get("textDisplay"), "score": sn.get("likeCount"),
        "url": f"https://www.youtube.com/watch?v={video_id}&lc={c['id']}",
    }


def video_comments(s, video_id, title, channel, target, max_comments):
    rows, token = [], None
    while len(rows) < max_comments:
        p = {"part": "snippet,replies", "videoId": video_id, "maxResults": 100,
             "textFormat": "plainText", "order": "time"}
        if token:
            p["pageToken"] = token
        try:
            res = call(s, "commentThreads", **p)
        except QuotaExceeded as e:
            e.partial = rows
            raise
        except Exception as e:  # comments disabled / private video -> 403
            print(f"  {video_id}: skipped ({e})")
            if not rows:
                rows = None  # signals "comments unavailable" to the caller
            break
        for th in res.get("items", []):
            top = th["snippet"]["topLevelComment"]
            rows.append(comment_row(top, video_id, title, channel, target))
            n_rep = th["snippet"].get("totalReplyCount", 0)
            inline = th.get("replies", {}).get("comments", [])
            if n_rep > len(inline):  # only up to 5 replies come inline
                try:
                    inline = all_replies(s, top["id"])
                except QuotaExceeded as e:
                    e.partial = rows
                    raise
                except Exception as e:
                    print(f"  {top['id']}: replies skipped ({e})")
            rows += [comment_row(r, video_id, title, channel, target, parent=top["id"])
                     for r in inline]
        token = res.get("nextPageToken")
        if not token:
            break
    return rows


def all_replies(s, parent_id):
    out, token = [], None
    while True:
        p = {"part": "snippet", "parentId": parent_id, "maxResults": 100, "textFormat": "plainText"}
        if token:
            p["pageToken"] = token
        res = call(s, "comments", **p)
        out += res.get("items", [])
        token = res.get("nextPageToken")
        if not token:
            return out


def main():
    t = load_targets()["youtube"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", nargs="*", default=t["queries"])
    ap.add_argument("--video-ids", nargs="*", default=t.get("video_ids", []))
    ap.add_argument("--channel-ids", nargs="*", default=t.get("channel_ids", []))
    ap.add_argument("--seed-file", help="CSV with a video_id column")
    ap.add_argument("--videos-per-query", type=int, default=10)
    ap.add_argument("--max-comments", type=int, default=2000, help="per video")
    ap.add_argument("--after", help="YYYY-MM-DD (video publish date, search only)")
    ap.add_argument("--before", help="YYYY-MM-DD")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    if "YOUTUBE_API_KEY" not in os.environ:
        ap.error("set YOUTUBE_API_KEY (see module docstring)")

    s = new_session()
    videos = {}  # video_id -> (title, channel, target)
    for q in a.queries:
        for vid, title, ch in search_videos(s, q, a.videos_per_query, t["region_code"],
                                            t["relevance_language"], a.after, a.before):
            videos.setdefault(vid, (title, ch, f"search~{q}"))
    for cid in a.channel_ids:
        for vid, title, ch in channel_uploads(s, cid, a.videos_per_query):
            videos.setdefault(vid, (title, ch, f"channel~{cid}"))
    if a.video_ids:
        for vid, (title, ch) in video_meta(s, a.video_ids).items():
            videos.setdefault(vid, (title, ch, "video_id"))
    status = []  # per-video outcome: metadata only, no comment text
    if a.seed_file:
        ids = pd.read_csv(a.seed_file).video_id.dropna().astype(str).unique().tolist()
        found = video_meta(s, ids)
        print(f"seed file: {len(found)} of {len(ids)} videos still available")
        status += [{"video_id": v, "available": 0, "comments_status": "video_unavailable"}
                   for v in ids if v not in found]
        for vid, (title, ch) in found.items():
            videos.setdefault(vid, (title, ch, f"seed:{os.path.basename(a.seed_file)}"))

    rows, done, quota_hit = [], set(), False
    try:
        for vid, (title, ch, target) in videos.items():
            got = video_comments(s, vid, title, ch, target, a.max_comments)
            print(f"  {vid} {title[:50]!r}: {len(got) if got is not None else 'unavailable'}")
            status.append({"video_id": vid, "available": 1, "title": title, "channel": ch,
                           "target": target, "comments_status":
                           "disabled_or_error" if got is None else "ok",
                           "comments_collected": len(got or [])})
            rows += got or []
            done.add(vid)
    except QuotaExceeded as e:
        quota_hit = True
        rows += getattr(e, "partial", [])
        print(f"QUOTA EXCEEDED on {e} -- stopping, saving partial results")
    tag = a.tag or "comments"
    path = save(rows, "youtube", tag)
    left = [v for v in videos if v not in done]
    status += [{"video_id": v, "available": 1, "title": videos[v][0], "channel": videos[v][1],
                "target": videos[v][2], "comments_status": "not_collected_quota"} for v in left]
    st = pd.DataFrame(status)
    st_path = OUT / "youtube" / f"youtube_{tag}_video_status.csv"
    st_path.parent.mkdir(parents=True, exist_ok=True)
    st.to_csv(st_path, index=False)
    print(f"~{UNITS['used']} quota units used; per-video status -> {st_path}")
    if path:
        print(f"output: {path}")
    if quota_hit:
        print(f"{len(left)} videos left for tomorrow (partially collected video included)")
        sys.exit(3)


if __name__ == "__main__":
    main()
