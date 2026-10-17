"""Size up every chat in the chat list without reading its history.

Usage: python scripts/tg_census.py telegram_chats.json data/telegram [--rate 3000]

For each chat: status, type, member count, creation date (from the "created" system
message when it survives), date of the oldest surviving message, date of the newest
message, and an approximate total message count. That count is the newest message's
number: Telegram numbers a channel's or supergroup's messages in order, so it is the
number of messages ever posted, including deleted ones (an upper bound). Small legacy
groups share numbering across the whole account, so no count is given for them.

Reads at most two messages' metadata per chat, no text, no media. Stop tg_collect.py
first: both use the same login file. Writes <out>/census.csv and prints totals with an
estimate of how long full collection would take at --rate messages per minute.
"""
import argparse, asyncio, csv, json, os, sys
from datetime import datetime, timezone

from telethon import TelegramClient, errors
from telethon.tl import types

sys.path.insert(0, os.path.dirname(__file__))
from tg_collect import chat_row  # noqa: E402
from tg_privacy import check_ready  # noqa: E402

FIELDS = ["alias", "cohort", "status", "type", "members", "created", "oldest_message",
          "newest_message", "approx_messages", "est_minutes", "paid_subscription",
          "request_needed", "error", "checked_at"]


async def census_row(client, chat, rate):
    _, row = await chat_row(client, chat["alias"], chat.get("cohort"), str(chat["chat"]))
    out = {"alias": chat["alias"], "cohort": chat.get("cohort"), "status": row["status"],
           "type": row.get("type", ""), "members": row.get("members", ""),
           "created": (row.get("created_date") or "")[:10],
           "oldest_message": (row.get("oldest_message_date") or "")[:10],
           "paid_subscription": int(bool(row.get("paid_subscription"))),
           "request_needed": int(bool(row.get("request_needed"))),
           "error": row.get("error", ""),
           "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if row["status"] == "ok":
        ref = str(chat["chat"])
        ent = await client.get_entity(int(ref) if ref.lstrip("-").isdigit() else ref)
        newest = await client.get_messages(ent, limit=1)
        if newest:
            out["newest_message"] = newest[0].date.date().isoformat()
            if isinstance(ent, types.Channel):  # per-chat numbering
                out["approx_messages"] = newest[0].id
                out["est_minutes"] = round(newest[0].id / rate, 1)
    return out


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("config")
    ap.add_argument("out")
    ap.add_argument("--rate", type=float, default=3000,
                    help="collection speed in messages per minute, for the time estimate")
    args = ap.parse_args()
    check_ready()
    api_id, api_hash = os.environ.get("TG_API_ID"), os.environ.get("TG_API_HASH")
    if not (api_id and api_hash):
        sys.exit("Set TG_API_ID and TG_API_HASH from https://my.telegram.org.")
    with open(args.config, encoding="utf-8") as f:
        chats = json.load(f)["chats"]

    client = TelegramClient(os.path.join(args.out, "research"), int(api_id), api_hash,
                            flood_sleep_threshold=600)
    client.session.save_entities = False
    await client.start()
    rows = []
    for i, chat in enumerate(chats, 1):
        try:
            r = await census_row(client, chat, args.rate)
        except errors.RPCError as exc:
            r = {"alias": chat["alias"], "cohort": chat.get("cohort"), "status": "error",
                 "error": type(exc).__name__}
        rows.append(r)
        print(f"[{i}/{len(chats)}] {r['alias']}: {r['status']}, "
              f"{r.get('members') or '?'} members, ~{r.get('approx_messages') or '?'} messages")
        await asyncio.sleep(1)
    await client.disconnect()

    path = os.path.join(args.out, "census.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    sized = [r for r in rows if r.get("approx_messages")]
    total = sum(r["approx_messages"] for r in sized)
    by_status = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    print(f"\nwrote {path}")
    print("status:", ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    print(f"about {total:,} messages in {len(sized)} sized chats (upper bound)")
    print(f"full collection at {args.rate:,.0f}/min: about {total / args.rate / 60:.1f} hours")
    for r in sorted(sized, key=lambda r: -r["approx_messages"])[:10]:
        print(f"  largest: {r['alias']:8} ~{r['approx_messages']:>10,} messages, "
              f"~{r['est_minutes'] / 60:.1f} h, since {r['oldest_message'] or '?'}")


if __name__ == "__main__":
    asyncio.run(main())
