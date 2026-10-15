"""Collect Reddit comments for threat / misogyny text mining.

Two backends:
  arctic   (default, no account needed) - the Arctic Shift Reddit archive
           (https://arctic-shift.photon-reddit.com), which mirrors public Reddit
           data for research. Supports keyword search inside comment bodies.
  official - Reddit's own OAuth API. Needs a "script" app from
           https://www.reddit.com/prefs/apps and env vars REDDIT_CLIENT_ID,
           REDDIT_CLIENT_SECRET. Reddit's API terms apply (non-commercial
           research use; respect deletions). Reddit has no comment-body search,
           so this backend only supports --mode threads.

Modes:
  keywords  comments in each subreddit whose body contains each keyword
  threads   full comment trees under posts whose title matches each query

Examples:
  python scripts/social/reddit_comments.py --mode keywords --after 2025-01-01
  python scripts/social/reddit_comments.py --mode threads --subreddits india TwoXIndia \
      --queries "woman journalist" --max-threads 50
"""
import argparse
import os
import time

import pandas as pd

from common import get_json, iso, load_targets, new_session, now, pseudonym, save

ARCTIC = "https://arctic-shift.photon-reddit.com/api"


def row(c, target, title=""):
    return {
        "platform": "reddit", "collected_at": now(), "target": target,
        "item_id": c.get("id"), "parent_id": c.get("parent_id"),
        "thread_id": c.get("link_id"), "thread_title": c.get("link_title") or title,
        "community": c.get("subreddit"), "created_at": iso(c.get("created_utc")),
        "author_hash": pseudonym(c.get("author")), "text": c.get("body"),
        "score": c.get("score"), "url": "https://www.reddit.com" + (c.get("permalink") or ""),
    }


def flatten(children, title, target, out):
    """Walk a nested Reddit comment listing (both APIs use the same shape)."""
    for ch in children or []:
        if ch.get("kind") != "t1":
            continue  # "more" stubs: not expanded
        c = ch["data"]
        if c.get("body") not in (None, "[deleted]", "[removed]"):
            out.append(row(c, target, title))
        rep = c.get("replies")
        if isinstance(rep, dict):
            flatten(rep["data"]["children"], title, target, out)


# ---------------------------------------------------------------- arctic shift
def windows(after, before, days):
    """Split [after, before) into `days`-long windows; Arctic Shift full-text
    search times out on long ranges of busy subreddits."""
    start = pd.Timestamp(after or pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=365))
    end = pd.Timestamp(before) if before else pd.Timestamp.now(tz="UTC")
    start, end = [t.tz_localize("UTC") if t.tzinfo is None else t for t in (start, end)]
    while start < end:
        stop = min(start + pd.Timedelta(days=days), end)
        yield int(start.timestamp()), int(stop.timestamp())
        start = stop


def arctic_keywords(s, subs, keywords, after, before, max_per, window_days):
    rows = []
    for sub in subs:
        for kw in keywords:
            n = 0
            for lo, hi in windows(after, before, window_days):
                cursor = lo
                while n < max_per:
                    p = {"subreddit": sub, "body": kw, "limit": 100, "sort": "asc",
                         "after": cursor, "before": hi}
                    try:
                        data = get_json(s, f"{ARCTIC}/comments/search", p).get("data") or []
                    except RuntimeError as e:
                        print(f"  r/{sub} '{kw}': {e}")
                        break
                    for c in data:
                        rows.append(row(c, f"r/{sub} body~{kw}"))
                    n += len(data)
                    if len(data) < 100:
                        break
                    cursor = int(data[-1]["created_utc"]) + 1
                    time.sleep(1)
                if n >= max_per:
                    break
            print(f"  r/{sub} '{kw}': {n}")
    return rows


def arctic_threads(s, subs, queries, after, before, max_threads):
    rows = []
    for sub in subs:
        for q in queries:
            p = {"subreddit": sub, "title": q, "limit": min(max_threads, 100), "sort": "desc"}
            if after:
                p["after"] = after
            if before:
                p["before"] = before
            posts = get_json(s, f"{ARCTIC}/posts/search", p).get("data") or []
            for post in posts[:max_threads]:
                tree = get_json(s, f"{ARCTIC}/comments/tree",
                                {"link_id": post["id"], "limit": 10000}).get("data") or []
                before_n = len(rows)
                flatten(tree, post.get("title", ""), f"r/{sub} title~{q}", rows)
                print(f"  r/{sub} '{q}' {post['id']}: {len(rows) - before_n} comments")
                time.sleep(1)
    return rows


# ---------------------------------------------------------------- official API
def official_session():
    s = new_session(os.environ.get("REDDIT_USER_AGENT", "threat-text-research/0.1"))
    r = s.post("https://www.reddit.com/api/v1/access_token",
               auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
               data={"grant_type": "client_credentials"}, timeout=60)
    r.raise_for_status()
    s.headers["Authorization"] = "bearer " + r.json()["access_token"]
    return s


def official_threads(s, subs, queries, max_threads):
    api, rows = "https://oauth.reddit.com", []
    for sub in subs:
        for q in queries:
            res = get_json(s, f"{api}/r/{sub}/search",
                           {"q": f'title:"{q}"', "restrict_sr": 1, "sort": "new",
                            "limit": min(max_threads, 100), "type": "link"})
            for post in [c["data"] for c in res["data"]["children"]][:max_threads]:
                listing = get_json(s, f"{api}/r/{sub}/comments/{post['id']}",
                                   {"limit": 500, "depth": 20})
                before_n = len(rows)
                for c in listing[1]["data"]["children"]:
                    if c.get("kind") == "t1":
                        c["data"].setdefault("link_id", "t3_" + post["id"])
                flatten(listing[1]["data"]["children"], post["title"], f"r/{sub} title~{q}", rows)
                print(f"  r/{sub} '{q}' {post['id']}: {len(rows) - before_n} comments")
                time.sleep(1)  # 100 requests/min limit
    return rows


def main():
    t = load_targets()["reddit"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["arctic", "official"], default="arctic")
    ap.add_argument("--mode", choices=["keywords", "threads"], default="keywords")
    ap.add_argument("--subreddits", nargs="+", default=t["subreddits"])
    ap.add_argument("--keywords", nargs="+", default=t["keywords"])
    ap.add_argument("--queries", nargs="+", default=t["thread_queries"])
    ap.add_argument("--after", help="YYYY-MM-DD")
    ap.add_argument("--before", help="YYYY-MM-DD")
    ap.add_argument("--max-per-keyword", type=int, default=2000)
    ap.add_argument("--max-threads", type=int, default=25)
    ap.add_argument("--window-days", type=int, default=30,
                    help="arctic keyword search is run in windows of this many days")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    if a.backend == "official":
        if a.mode != "threads":
            ap.error("the official API has no comment search; use --mode threads")
        rows = official_threads(official_session(), a.subreddits, a.queries, a.max_threads)
    elif a.mode == "keywords":
        rows = arctic_keywords(new_session(), a.subreddits, a.keywords, a.after, a.before,
                               a.max_per_keyword, a.window_days)
    else:
        rows = arctic_threads(new_session(), a.subreddits, a.queries, a.after, a.before,
                              a.max_threads)
    save(rows, "reddit", a.tag or a.mode)


if __name__ == "__main__":
    main()
