"""Shared helpers for the Reddit / YouTube / Telegram comment collectors.

Every collector writes rows with the same columns (COLS) to
data/social_raw/<platform>/<platform>_<tag>_<timestamp>.csv.gz. That folder is
git-ignored: it holds personal data (comments by identifiable people) and
should stay on your machine / secure storage, not in a public repo.

Usernames are never stored. They are replaced by an HMAC-SHA256 pseudonym keyed
with SOCIAL_HASH_SALT (env var) or a random salt kept in data/social_raw/.salt,
so the same author gets the same pseudonym across runs without being
recoverable from the data.
"""
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data" / "social_raw"
TARGETS = Path(__file__).resolve().parent / "targets.json"

sys.path.insert(0, str(REPO / "scripts"))
from build_threat_corpus import HINGLISH_THREAT_RE, RAPE_RE, is_hinglish  # noqa: E402

COLS = ["platform", "collected_at", "target", "item_id", "parent_id", "thread_id",
        "thread_title", "community", "created_at", "author_hash", "text", "score", "url",
        "rape_lexicon", "hinglish_threat_lexicon", "hinglish"]


def load_targets():
    return json.loads(TARGETS.read_text())


def _salt():
    if os.environ.get("SOCIAL_HASH_SALT"):
        return os.environ["SOCIAL_HASH_SALT"].encode()
    p = OUT / ".salt"
    if not p.exists():
        OUT.mkdir(parents=True, exist_ok=True)
        p.write_text(secrets.token_hex(32))
    return p.read_text().strip().encode()


_SALT = None


def pseudonym(author):
    global _SALT
    if author in (None, "", "[deleted]", "[removed]"):
        return ""
    _SALT = _SALT or _salt()
    return hmac.new(_SALT, str(author).encode(), hashlib.sha256).hexdigest()[:16]


def iso(ts):
    """Unix seconds or ISO string -> ISO-8601 UTC string."""
    if ts is None or ts == "":
        return ""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, timezone.utc).isoformat()
    t = pd.Timestamp(ts)
    return (t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")).isoformat()


def get_json(session, url, params=None, headers=None, tries=5, wait=2.0):
    """GET with retry/back-off on 429, 5xx and API 'slow down' errors."""
    for i in range(tries):
        r = session.get(url, params=params, headers=headers, timeout=120)
        busy = r.status_code in (429, 500, 502, 503, 504)
        if r.status_code == 422 and any(w in r.text.lower() for w in ("timeout", "slow down")):
            busy = True  # Arctic Shift: query timed out server-side
        if busy:
            time.sleep(wait * 2 ** i)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"giving up on {url} {params}")


def new_session(user_agent="threat-text-research/0.1 (academic research)"):
    s = requests.Session()
    s.headers["User-Agent"] = user_agent
    return s


def save(rows, platform, tag):
    """Add keyword flags, de-duplicate and write a gzipped CSV. Returns the path."""
    df = pd.DataFrame(rows, columns=[c for c in COLS if c not in
                                     ("rape_lexicon", "hinglish_threat_lexicon", "hinglish")])
    if df.empty:
        print(f"{platform}: nothing collected")
        return None
    df = df.drop_duplicates(["platform", "item_id"])
    df["text"] = df.text.fillna("")
    df["rape_lexicon"] = df.text.str.contains(RAPE_RE).astype(int)
    df["hinglish_threat_lexicon"] = df.text.str.contains(HINGLISH_THREAT_RE).astype(int)
    df["hinglish"] = df.text.map(is_hinglish).astype(int)
    out = OUT / platform
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M")
    path = out / f"{platform}_{tag}_{stamp}.csv.gz"
    df[COLS].to_csv(path, index=False, compression="gzip")
    print(f"{platform}: {len(df)} rows -> {path.relative_to(REPO)} "
          f"(rape_lexicon={df.rape_lexicon.sum()}, hinglish_threat={df.hinglish_threat_lexicon.sum()}, "
          f"hinglish={df.hinglish.sum()})")
    return path


def now():
    return datetime.now(timezone.utc).isoformat()
