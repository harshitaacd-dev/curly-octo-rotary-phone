"""Collect messages from public Telegram channels / groups.

Two modes:
  --web   no account needed. Reads the public web preview t.me/s/<channel>.
          Gives channel POSTS only (no comments) for channels that allow
          the preview.
  default Telethon (MTProto) login as a normal Telegram user. Reads channel
          posts AND the comments in each post's linked discussion group, or
          every message of a public group. Needs api_id / api_hash from
          https://my.telegram.org -> API development tools:
              export TELEGRAM_API_ID=... TELEGRAM_API_HASH=...
              pip install telethon
          The first run asks for your phone number and login code; the session
          is stored in data/social_raw/.telegram.session (git-ignored).
          Only read public channels/groups, and collect at a gentle rate.

Examples:
  python scripts/social/telegram_comments.py --web --channels somechannel --max-posts 300
  python scripts/social/telegram_comments.py --channels somechannel --max-posts 200 \
      --max-comments 500 --after 2025-01-01
"""
import argparse
import asyncio
import html
import os
import re
import time

from common import OUT, get_json, iso, load_targets, new_session, now, pseudonym, save  # noqa: F401


# ------------------------------------------------------------------ web preview
POST_RE = re.compile(r'data-post="([^"/]+)/(\d+)"(.*?)(?=data-post="|\Z)', re.S)
TEXT_RE = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
TIME_RE = re.compile(r'<time[^>]*datetime="([^"]+)"')
VIEWS_RE = re.compile(r'tgme_widget_message_views">([^<]+)<')


def strip_tags(h):
    h = re.sub(r"<br\s*/?>", "\n", h)
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def web_channel(s, channel, max_posts):
    rows, before = [], None
    while len(rows) < max_posts:
        r = s.get(f"https://t.me/s/{channel}", params={"before": before} if before else None,
                  timeout=60)
        r.raise_for_status()
        posts = POST_RE.findall(r.text)
        if not posts:
            break
        for ch, pid, body in posts:
            m = TEXT_RE.search(body)
            if not m:
                continue  # media-only post
            t, v = TIME_RE.search(body), VIEWS_RE.search(body)
            rows.append({
                "platform": "telegram", "collected_at": now(), "target": f"web:{channel}",
                "item_id": f"{ch}/{pid}", "parent_id": "", "thread_id": f"{ch}/{pid}",
                "thread_title": "", "community": ch, "created_at": iso(t.group(1)) if t else "",
                "author_hash": pseudonym(ch), "text": strip_tags(m.group(1)),
                "score": v.group(1) if v else "", "url": f"https://t.me/{ch}/{pid}",
            })
        oldest = min(int(p[1]) for p in posts)
        if before is not None and oldest >= before:
            break
        before = oldest
        time.sleep(2)
    print(f"  {channel}: {len(rows)} posts")
    return rows[:max_posts]


# ------------------------------------------------------------------ Telethon
def msg_row(m, chat_name, target, thread_id, thread_title, parent=""):
    sender = getattr(m, "sender_id", None) or getattr(m, "post_author", None)
    return {
        "platform": "telegram", "collected_at": now(), "target": target,
        "item_id": f"{chat_name}/{m.id}", "parent_id": parent, "thread_id": thread_id,
        "thread_title": thread_title, "community": chat_name, "created_at": iso(m.date),
        "author_hash": pseudonym(sender), "text": m.message or "",
        "score": getattr(m, "views", None) or "",
        "url": f"https://t.me/{chat_name}/{m.id}",
    }


async def telethon_collect(channels, max_posts, max_comments, after):
    from telethon import TelegramClient
    from telethon.errors import MsgIdInvalidError

    OUT.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(OUT / ".telegram"), int(os.environ["TELEGRAM_API_ID"]),
                            os.environ["TELEGRAM_API_HASH"])
    rows = []
    async with client:
        for name in channels:
            ent = await client.get_entity(name)
            chat = getattr(ent, "username", None) or str(ent.id)
            is_channel = getattr(ent, "broadcast", False)
            n_posts = n_comments = 0
            async for m in client.iter_messages(ent, limit=max_posts):
                if after and m.date.date().isoformat() < after:
                    break
                post_id = f"{chat}/{m.id}"
                if m.message:
                    rows.append(msg_row(m, chat, f"tg:{name}", post_id, ""))
                    n_posts += 1
                if is_channel and m.replies and m.replies.comments and m.replies.replies:
                    try:
                        async for c in client.iter_messages(ent, reply_to=m.id, limit=max_comments):
                            if c.message:
                                rows.append(msg_row(c, f"{chat}#comments", f"tg:{name}",
                                                    post_id, (m.message or "")[:200], parent=post_id))
                                n_comments += 1
                    except MsgIdInvalidError:
                        pass
            print(f"  {name}: {n_posts} posts/messages, {n_comments} comments")
    return rows


def main():
    t = load_targets()["telegram"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", nargs="+", default=t["channels"])
    ap.add_argument("--web", action="store_true", help="public web preview, posts only, no login")
    ap.add_argument("--max-posts", type=int, default=500)
    ap.add_argument("--max-comments", type=int, default=1000, help="per post (Telethon mode)")
    ap.add_argument("--after", help="YYYY-MM-DD (Telethon mode)")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    if not a.channels:
        ap.error("no channels: pass --channels or fill telegram.channels in targets.json")

    if a.web:
        s = new_session()
        rows = [r for ch in a.channels for r in web_channel(s, ch, a.max_posts)]
    else:
        if "TELEGRAM_API_ID" not in os.environ:
            ap.error("set TELEGRAM_API_ID / TELEGRAM_API_HASH, or use --web")
        rows = asyncio.run(telethon_collect(a.channels, a.max_posts, a.max_comments, a.after))
    save(rows, "telegram", a.tag or ("web" if a.web else "messages"))


if __name__ == "__main__":
    main()
