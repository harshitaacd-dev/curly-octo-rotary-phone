"""Find candidate public groups, channels and bots with Telegram's own search.

Usage: python scripts/tg_find.py TERMS.txt data/telegram [--config telegram_chats.json]

TERMS.txt holds one search term per line, optionally followed by a tab and the cohort
it is meant for (e.g. "some term<TAB>hindi"); lines starting with # are skipped. Keep it
next to the chat list: it is git-ignored and deleted by tg_purge.py.

Uses the research account (same TG_API_ID / TG_API_HASH / TG_SALT and session as
tg_collect.py) and Telegram's public directory search (contacts.Search). That search
only matches names and @usernames of public chats and bots. It returns no messages and
no media, and this script fetches none: per chat it reads only the title, @username,
description, member count, type and creation date. It never joins anything; screening
and joining are done by hand. People found by the search are dropped, never stored.

Writes, inside the output folder:
  candidates.csv   one row per chat or bot found: link, title, description, members,
                   type, creation date, flags, the terms and dates that found it, and
                   whether it is already in the chat list. Add your screening decision
                   in the `decision` column; it is kept when the script is run again.
  search_log.csv   one row per search: when, term, cohort, results (the search log for
                   the methods section)
"""
import argparse, asyncio, csv, json, os, sys
from datetime import datetime, timezone

from telethon import TelegramClient, errors
from telethon.tl import types
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.contacts import SearchRequest

sys.path.insert(0, os.path.dirname(__file__))
from tg_privacy import check_ready  # noqa: E402

FIELDS = ["link", "kind", "title", "description", "members", "created", "verified", "scam",
          "fake", "restricted", "found_by", "cohorts", "first_found", "last_found",
          "in_chat_list", "decision"]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_terms(path):
    terms = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.strip() and not line.lstrip().startswith("#"):
                term, _, cohort = line.partition("\t")
                terms.append((term.strip(), cohort.strip()))
    return terms


def norm(ref):
    """'https://t.me/X', 'telegram.me/X', '@X' and 'X' all become 't.me/x'."""
    r = ref.strip().lower().removeprefix("https://").removeprefix("http://")
    r = r.replace("telegram.me/", "t.me/").removeprefix("@")
    return r if "/" in r else "t.me/" + r


def known_links(config):
    """Chats already in the chat list, as normalised links (numeric ids cannot be matched)."""
    if not config or not os.path.exists(config):
        return set()
    with open(config, encoding="utf-8") as f:
        return {norm(str(c["chat"])) for c in json.load(f)["chats"]
                if not str(c["chat"]).lstrip("-").isdigit()}


async def describe(client, chat):
    """Row for a public channel or group found by search (metadata only)."""
    about, members = "", getattr(chat, "participants_count", None)
    try:
        full = (await client(GetFullChannelRequest(chat))).full_chat
        about, members = full.about or "", full.participants_count or members
    except errors.RPCError:
        pass
    return {
        "link": f"t.me/{chat.username}", "title": chat.title,
        "kind": "channel" if chat.broadcast else "forum" if getattr(chat, "forum", False) else "group",
        "description": " ".join(about.split())[:500], "members": members,
        # For a chat the account is not in, Telegram's `date` is its creation date.
        "created": chat.date.date().isoformat() if chat.date and chat.left else "",
        "verified": int(bool(chat.verified)), "scam": int(bool(chat.scam)),
        "fake": int(bool(chat.fake)), "restricted": int(bool(chat.restricted)),
    }


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("terms")
    ap.add_argument("out")
    ap.add_argument("--config", help="chat list, to mark chats already included")
    ap.add_argument("--limit", type=int, default=50, help="results asked for per term")
    ap.add_argument("--pause", type=float, default=5, help="seconds between searches")
    args = ap.parse_args()
    check_ready()
    api_id, api_hash = os.environ.get("TG_API_ID"), os.environ.get("TG_API_HASH")
    if not (api_id and api_hash):
        sys.exit("Set TG_API_ID and TG_API_HASH from https://my.telegram.org.")
    os.makedirs(args.out, exist_ok=True)
    cand_path = os.path.join(args.out, "candidates.csv")
    log_path = os.path.join(args.out, "search_log.csv")

    rows = {}
    if os.path.exists(cand_path):
        with open(cand_path, encoding="utf-8") as f:
            rows = {r["link"]: r for r in csv.DictReader(f)}
    known = known_links(args.config)
    new_log = not os.path.exists(log_path)

    client = TelegramClient(os.path.join(args.out, "research"), int(api_id), api_hash,
                            flood_sleep_threshold=600)
    client.session.save_entities = False
    await client.start()
    with open(log_path, "a", newline="", encoding="utf-8") as lf:
        log = csv.writer(lf)
        if new_log:
            log.writerow(["searched_at", "term", "cohort", "chats", "bots", "new"])
        for term, cohort in read_terms(args.terms):
            stamp = now()
            found = await client(SearchRequest(q=term, limit=args.limit))
            hits = []
            for chat in found.chats:
                if isinstance(chat, types.Channel) and chat.username:
                    hits.append(await describe(client, chat))
            for user in found.users:  # only bots are kept; people are dropped unread
                if isinstance(user, types.User) and user.bot and user.username:
                    hits.append({"link": f"t.me/{user.username}", "kind": "bot",
                                 "title": "", "description": "", "members": "",
                                 "created": "", "verified": int(bool(user.verified)),
                                 "scam": int(bool(user.scam)), "fake": int(bool(user.fake)),
                                 "restricted": int(bool(user.restricted))})
            new = 0
            for h in hits:
                r = rows.get(h["link"])
                if r is None:
                    new += 1
                    r = rows[h["link"]] = {**h, "found_by": "", "cohorts": "",
                                           "first_found": stamp[:10], "decision": ""}
                else:
                    r.update({k: v for k, v in h.items() if v not in ("", None)})
                r["found_by"] = ";".join(sorted(set(filter(None, r["found_by"].split(";"))) | {term}))
                r["cohorts"] = ";".join(sorted(set(filter(None, r["cohorts"].split(";"))) | ({cohort} - {""})))
                r["last_found"] = stamp[:10]
            log.writerow([stamp, term, cohort, sum(h["kind"] != "bot" for h in hits),
                          sum(h["kind"] == "bot" for h in hits), new])
            lf.flush()
            print(f"{term!r}: {len(hits)} found, {new} new")
            await asyncio.sleep(args.pause)
    await client.disconnect()

    for r in rows.values():
        r["in_chat_list"] = int(r["link"].lower() in known)
    with open(cand_path + ".tmp", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: (r["kind"] == "bot", -int(r["members"] or 0))))
    os.replace(cand_path + ".tmp", cand_path)
    print(f"wrote {cand_path} ({len(rows)} candidates)")


if __name__ == "__main__":
    asyncio.run(main())
