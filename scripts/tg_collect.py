"""Collect message metadata from Telegram groups and channels the research account has joined.

Usage: python scripts/tg_collect.py CONFIG.json data/telegram [--revisit-days 7]

Needs TG_API_ID and TG_API_HASH (from my.telegram.org) and TG_SALT (a long random string,
kept outside the repo and identical on every run, or user hashes will not line up).
The first run asks for the account's phone number and login code and saves a .session
file in the output folder.

CONFIG.json lists the chats, each already joined by hand in the Telegram app (this
script never joins anything):
  {"chats": [{"alias": "HI-01", "cohort": "hindi", "chat": "https://t.me/+AbCdEf..."},
             {"alias": "TA-01", "cohort": "tamil", "chat": "-1001234567890"}]}

Media is never downloaded. Only its type, size and a hashed Telegram file id are kept, so
the same file can be traced when it is forwarded or re-sent between chats (a fresh upload
of the same image gets a new id and is not matched). User, chat and bot ids are stored as
salted HMACs. Message text is kept as is: it is the material for the qualitative coding,
and the output folder must stay out of git and be deleted when the project ends.

Each run appends snapshots to <out>/messages.jsonl and <out>/chats.jsonl:
  - every message newer than the last run;
  - messages from the last --revisit-days days again when they were edited since, or
    with "deleted": true when they are gone;
  - one row per chat with its title, size and status, so renames, bans and re-openings
    under the same name show up over time.
"""
import argparse, asyncio, hashlib, hmac, json, os, sys
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient, errors, utils
from telethon.tl import types
from telethon.tl.functions.channels import GetFullChannelRequest

SALT = os.environ.get("TG_SALT", "").encode()


def anon(value):
    """Salted HMAC of an id, 16 hex characters; None stays None."""
    if value is None:
        return None
    return hmac.new(SALT, str(value).encode(), hashlib.sha256).hexdigest()[:16]


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def peer_hash(peer):
    return anon(utils.get_peer_id(peer)) if peer else None


def media_info(media):
    """(kind, mime, size, hashed file id) without fetching the file."""
    if isinstance(media, types.MessageMediaPhoto) and media.photo:
        sizes = [s.size for s in getattr(media.photo, "sizes", []) if hasattr(s, "size")]
        return "photo", "image/jpeg", max(sizes, default=None), anon(f"p{media.photo.id}")
    if isinstance(media, types.MessageMediaDocument) and media.document:
        doc, kind = media.document, "document"
        for a in getattr(doc, "attributes", []):
            if isinstance(a, types.DocumentAttributeSticker):
                kind = "sticker"
            elif isinstance(a, types.DocumentAttributeVideo):
                kind = "round_video" if a.round_message else "video"
            elif isinstance(a, types.DocumentAttributeAudio):
                kind = "voice" if a.voice else "audio"
            elif isinstance(a, types.DocumentAttributeAnimated):
                kind = "gif"
        return kind, getattr(doc, "mime_type", None), getattr(doc, "size", None), anon(f"d{doc.id}")
    if media is None:
        return None, None, None, None
    return type(media).__name__.replace("MessageMedia", "").lower(), None, None, None


def message_row(alias, cohort, m):
    kind, mime, size, key = media_info(m.media)
    fwd, reply = m.fwd_from, m.reply_to
    urls = [e.url for e in (m.entities or []) if isinstance(e, types.MessageEntityTextUrl)]
    markup = m.reply_markup if isinstance(m.reply_markup, types.ReplyInlineMarkup) else None
    # URL buttons: KeyboardButtonUrl in older Telethon layers, KeyboardButton(type=...Url) in newer
    buttons = [u for r in (markup.rows if markup else []) for b in r.buttons
               if (u := getattr(b, "url", None) or getattr(getattr(b, "type", None), "url", None))]
    return {
        "chat": alias, "cohort": cohort, "msg_id": m.id, "date": iso(m.date),
        "edit_date": iso(m.edit_date), "deleted": False,
        "sender": anon(m.sender_id), "via_bot": anon(m.via_bot_id), "post_author": m.post_author,
        "fwd_from": peer_hash(fwd.from_id) if fwd else None,
        "fwd_from_name": fwd.from_name if fwd else None,
        "fwd_date": iso(fwd.date) if fwd else None,
        "reply_to": reply.reply_to_msg_id if isinstance(reply, types.MessageReplyHeader) else None,
        "topic": (reply.reply_to_top_id or reply.reply_to_msg_id)
        if isinstance(reply, types.MessageReplyHeader) and reply.forum_topic else None,
        "grouped_id": m.grouped_id, "text": m.message or "",
        "hidden_urls": urls, "button_urls": buttons,
        "media_kind": kind, "media_mime": mime, "media_size": size, "media_key": key,
        "views": m.views, "forwards": m.forwards,
        "replies": m.replies.replies if m.replies else None,
        "collected_at": iso(datetime.now(timezone.utc)),
    }


async def chat_row(client, alias, cohort, ref):
    """Resolve a chat and describe it; returns (entity or None, row)."""
    row = {"chat": alias, "cohort": cohort, "collected_at": iso(datetime.now(timezone.utc))}
    try:
        ent = await client.get_entity(int(ref) if ref.lstrip("-").isdigit() else ref)
    except (ValueError, errors.RPCError) as exc:
        row.update(status="unavailable", error=type(exc).__name__)
        return None, row
    if isinstance(ent, types.ChatInvite):  # an invite link the account has not joined
        row.update(status="not_joined", title=ent.title)
        return None, row
    size = getattr(ent, "participants_count", None)
    if isinstance(ent, types.Channel):
        try:
            size = (await client(GetFullChannelRequest(ent))).full_chat.participants_count
        except errors.RPCError:
            pass
    row.update(
        status="ok", chat_hash=anon(utils.get_peer_id(ent)), title=getattr(ent, "title", None),
        username=getattr(ent, "username", None), members=size,
        type="channel" if getattr(ent, "broadcast", False)
        else "forum" if getattr(ent, "forum", False) else "group",
        scam=getattr(ent, "scam", False), fake=getattr(ent, "fake", False),
        restricted=getattr(ent, "restricted", False),
    )
    return ent, row


async def collect(client, chat, state, revisit_days, out_msgs):
    alias, cohort = chat["alias"], chat.get("cohort")
    ent, row = await chat_row(client, alias, cohort, str(chat["chat"]))
    if ent is None:
        print(f"{alias}: {row['status']}", file=sys.stderr)
        return row, 0
    st = state.setdefault(alias, {"max_id": 0, "recent": {}})
    since = datetime.now(timezone.utc) - timedelta(days=revisit_days)
    # msg_id -> [date, edit_date] for earlier messages still inside the revisit window
    recent = {k: v for k, v in st["recent"].items() if v[0] >= iso(since)}
    top, written, seen = st["max_id"], 0, set()

    # Newest first: everything after the last run, then the revisit window again.
    async for m in client.iter_messages(ent):
        if m.id <= top and m.date < since:
            break
        if not isinstance(m, types.Message):  # service messages (joins, pins, ...)
            continue
        mid = str(m.id)
        seen.add(mid)
        if m.id > top or (mid in recent and recent[mid][1] != iso(m.edit_date)):
            out_msgs.write(json.dumps(message_row(alias, cohort, m), ensure_ascii=False) + "\n")
            written += 1
        if m.date >= since:
            recent[mid] = [iso(m.date), iso(m.edit_date)]
        st["max_id"] = max(st["max_id"], m.id)

    stamp = iso(datetime.now(timezone.utc))
    for mid in [k for k in recent if k not in seen]:
        out_msgs.write(json.dumps({"chat": alias, "cohort": cohort, "msg_id": int(mid),
                                   "deleted": True, "collected_at": stamp}) + "\n")
        del recent[mid]
        written += 1
    st["recent"] = recent
    return row, written


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("config")
    ap.add_argument("out")
    ap.add_argument("--revisit-days", type=int, default=7)
    args = ap.parse_args()
    if len(SALT) < 16:
        sys.exit("Set TG_SALT to a random string of at least 16 characters (and keep it).")
    api_id, api_hash = os.environ.get("TG_API_ID"), os.environ.get("TG_API_HASH")
    if not (api_id and api_hash):
        sys.exit("Set TG_API_ID and TG_API_HASH from https://my.telegram.org.")

    with open(args.config, encoding="utf-8") as f:
        chats = json.load(f)["chats"]
    os.makedirs(args.out, exist_ok=True)
    state_path = os.path.join(args.out, "state.json")
    state = json.load(open(state_path)) if os.path.exists(state_path) else {}

    client = TelegramClient(os.path.join(args.out, "research"), int(api_id), api_hash,
                            flood_sleep_threshold=600)
    await client.start()
    with open(os.path.join(args.out, "messages.jsonl"), "a", encoding="utf-8") as msgs, \
         open(os.path.join(args.out, "chats.jsonl"), "a", encoding="utf-8") as chat_log:
        for chat in chats:
            row, n = await collect(client, chat, state, args.revisit_days, msgs)
            chat_log.write(json.dumps(row, ensure_ascii=False) + "\n")
            msgs.flush()
            print(f"{chat['alias']}: {row['status']}, {n} message snapshots")
            with open(state_path + ".tmp", "w") as f:
                json.dump(state, f)
            os.replace(state_path + ".tmp", state_path)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
