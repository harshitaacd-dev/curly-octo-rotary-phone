"""Summaries, link coding and network files from the Telegram collection.

Usage: python scripts/tg_analyse.py data/telegram data/telegram/out [--codes coded_domains.csv]

Reads <in>/messages.jsonl and <in>/chats.jsonl from scripts/tg_collect.py, keeps the
latest snapshot of each message, and writes to <out>:
  chat_summary.csv     per chat: messages, active senders, media files, distinct media,
                       edits and deletions seen, title changes, last status and size
  cohort_overlap.csv   per pair of cohorts (e.g. languages): shared senders and media,
                       and the share of each cohort's media also seen in the other
  chat_overlap.csv     the same for every pair of chats
  links.csv            every URL in text, hidden links and buttons, with its domain and
                       platform category ("uncoded" until coded; see --codes)
  domains.csv          per domain: category, links, messages, chats, senders
  payments.csv         messages naming a possible UPI ID, upi:// link or payment page
                       (the ID itself only as a salted hash)
  gephi_nodes.csv,     sender-chat network for Gephi (Source = hashed sender, Target =
  gephi_edges.csv      chat alias, Weight = messages)

--codes takes a CSV with columns domain,category for domains you have coded by hand;
it overrides the built-in list. Keep the categories from AI Forensics' Table 1 so the
results compare (Archive/File Hosting, E-Commerce, Gambling, Government Site, Messenger,
NCII AI Image & Video Generator, Porn Site, Search Engine, Sex Games, Social Media,
Streaming Site, Telegram Redirect), plus Telegram and Payment.
"""
import argparse, csv, hashlib, hmac, json, os, re, sys
from collections import Counter, defaultdict
from itertools import combinations
from urllib.parse import urlsplit

SALT = os.environ.get("TG_SALT", "").encode()

CATEGORIES = {
    "Social Media": ["tiktok.com", "instagram.com", "facebook.com", "fb.com", "fb.watch",
                     "x.com", "twitter.com", "reddit.com", "redd.it", "youtube.com", "youtu.be",
                     "snapchat.com", "sharechat.com", "mojapp.in", "joshapp.in", "threads.net",
                     "linkedin.com", "pinterest.com", "koo.in", "chingari.io", "onlyfans.com"],
    "Messenger": ["whatsapp.com", "wa.me", "discord.gg", "discord.com", "signal.group",
                  "signal.me"],
    "Telegram": ["t.me", "telegram.me", "telegram.dog", "telegram.org"],
    "Archive/File Hosting": ["mega.nz", "mega.io", "drive.google.com", "docs.google.com",
                             "terabox.com", "teraboxapp.com", "1024terabox.com", "mediafire.com",
                             "gofile.io", "dropbox.com", "pixeldrain.com", "files.fm",
                             "workupload.com", "krakenfiles.com", "imgur.com", "postimg.cc"],
    "Payment": ["paypal.me", "paypal.com", "razorpay.me", "rzp.io", "pages.razorpay.com",
                "instamojo.com", "paytm.me", "p.paytm.me", "cosmofeed.com", "superprofile.bio",
                "buymeacoffee.com", "ko-fi.com", "patreon.com"],
    "Search Engine": ["google.com", "bing.com", "duckduckgo.com"],
    "Government Site": ["gov.in", "nic.in"],
}
DOMAIN_CATEGORY = {d: c for c, ds in CATEGORIES.items() for d in ds}

URL_RE = re.compile(r"(?:https?://|www\.|upi://)[^\s<>\"'\]\)]+|\b(?:t\.me|wa\.me)/[^\s<>\"'\]\)]+",
                    re.I)
# Virtual payment address: handle@bank with no dot after the bank part (unlike an email).
UPI_RE = re.compile(r"(?<![\w.@])[\w.\-]{2,64}@[a-z]{2,20}(?![\w.@])", re.I)
PAY_WORDS = re.compile(r"\b(upi|gpay|google ?pay|phonepe|paytm|bhim|qr|scan|paid|payment|"
                       r"price|rs\.?|inr|₹|crypto|usdt|btc)\b", re.I)


def anon(value):
    return hmac.new(SALT, str(value).encode(), hashlib.sha256).hexdigest()[:16]


def domain_of(url):
    if url.lower().startswith("upi://"):
        return "upi"
    host = urlsplit(url if "://" in url else "http://" + url).hostname or ""
    return host.lower().removeprefix("www.").removeprefix("m.")


def categorise(domain, codes):
    if domain == "upi":
        return "Payment"
    parts = domain.split(".")
    for i in range(len(parts) - 1):  # most specific suffix first: pages.razorpay.com, gov.in
        suffix = ".".join(parts[i:])
        if suffix in codes:
            return codes[suffix]
        if suffix in DOMAIN_CATEGORY:
            return DOMAIN_CATEGORY[suffix]
    return "uncoded"


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


def overlap_rows(groups, senders, media):
    rows = []
    for a, b in combinations(sorted(groups), 2):
        s, m = senders[a] & senders[b], media[a] & media[b]
        rows.append([a, b, len(senders[a]), len(senders[b]), len(s),
                     len(media[a]), len(media[b]), len(m),
                     round(len(m) / len(media[a]), 4) if media[a] else "",
                     round(len(m) / len(media[b]), 4) if media[b] else ""])
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--codes", help="CSV with domain,category for hand-coded domains")
    args = ap.parse_args()
    if len(SALT) < 16:
        sys.exit("Set TG_SALT to the same value used for collection.")
    codes = {}
    if args.codes:
        with open(args.codes, encoding="utf-8") as f:
            codes = {r["domain"].strip().lower(): r["category"].strip() for r in csv.DictReader(f)}
    os.makedirs(args.out, exist_ok=True)

    # Latest snapshot per message; count edits and deletions on the way.
    latest, edits, deleted = {}, Counter(), Counter()
    for r in load(os.path.join(args.src, "messages.jsonl")):
        key = (r["chat"], r["msg_id"])
        if r.get("deleted"):
            deleted[r["chat"]] += 1
            if key in latest:
                latest[key]["deleted"] = True
            continue
        if key in latest:
            edits[r["chat"]] += 1
        latest[key] = r
    msgs = [r for r in latest.values() if "date" in r]

    chats = defaultdict(list)
    for r in load(os.path.join(args.src, "chats.jsonl")):
        chats[r["chat"]].append(r)

    # Per chat and per cohort sets.
    by_chat = defaultdict(list)
    for r in msgs:
        by_chat[r["chat"]].append(r)
    sender_sets, media_sets = defaultdict(set), defaultdict(set)
    cohort_senders, cohort_media = defaultdict(set), defaultdict(set)
    media_chats = defaultdict(set)
    for r in msgs:
        if r.get("sender"):
            sender_sets[r["chat"]].add(r["sender"])
            cohort_senders[r.get("cohort") or "-"].add(r["sender"])
        if r.get("media_key"):
            media_sets[r["chat"]].add(r["media_key"])
            cohort_media[r.get("cohort") or "-"].add(r["media_key"])
            media_chats[r["media_key"]].add(r["chat"])

    rows = []
    for alias in sorted(set(by_chat) | set(chats)):
        ms, snaps = by_chat.get(alias, []), chats.get(alias, [])
        last = snaps[-1] if snaps else {}
        titles = [s.get("title") for s in snaps if s.get("title")]
        dates = sorted(r["date"] for r in ms)
        rows.append([alias, last.get("cohort"), last.get("type"), last.get("status"),
                     last.get("members"), len(ms), len(sender_sets[alias]),
                     sum(1 for r in ms if r.get("media_key")), len(media_sets[alias]),
                     sum(1 for k in media_sets[alias] if len(media_chats[k]) > 1),
                     edits[alias], deleted[alias],
                     sum(1 for a, b in zip(titles, titles[1:]) if a != b),
                     dates[0] if dates else "", dates[-1] if dates else ""])
    write(os.path.join(args.out, "chat_summary.csv"),
          ["chat", "cohort", "type", "last_status", "members", "messages", "active_senders",
           "media_messages", "distinct_media", "media_also_elsewhere", "edits_seen",
           "deletions_seen", "title_changes", "first_message", "last_message"], rows)

    total_media = len(media_chats)
    shared = sum(1 for cs in media_chats.values() if len(cs) > 1)
    print(f"{len(msgs)} messages, {len(set().union(*sender_sets.values()) if sender_sets else set())}"
          f" active senders, {total_media} distinct media, {shared} seen in more than one chat")

    head = ["a", "b", "senders_a", "senders_b", "shared_senders", "media_a", "media_b",
            "shared_media", "share_of_a_media", "share_of_b_media"]
    write(os.path.join(args.out, "cohort_overlap.csv"), head,
          overlap_rows(cohort_senders.keys() | cohort_media.keys(), cohort_senders, cohort_media))
    write(os.path.join(args.out, "chat_overlap.csv"), head,
          overlap_rows(sender_sets.keys() | media_sets.keys(), sender_sets, media_sets))

    # Links and payment mentions.
    link_rows, pay_rows = [], []
    dom = defaultdict(lambda: {"links": 0, "msgs": set(), "chats": set(), "senders": set()})
    for r in sorted(msgs, key=lambda r: (r["chat"], r["msg_id"])):
        text = r.get("text") or ""
        found = [(u.rstrip(".,;:!?"), "text") for u in URL_RE.findall(text)]
        found += [(u, "hidden") for u in r.get("hidden_urls") or []]
        found += [(u, "button") for u in r.get("button_urls") or []]
        for url, where in found:
            d = domain_of(url)
            cat = categorise(d, codes)
            link_rows.append([r["chat"], r.get("cohort"), r["msg_id"], r["date"], r.get("sender"),
                              where, url, d, cat])
            s = dom[d]
            s["links"] += 1
            s["msgs"].add((r["chat"], r["msg_id"]))
            s["chats"].add(r["chat"])
            if r.get("sender"):
                s["senders"].add(r["sender"])
            if cat == "Payment":
                pay_rows.append([r["chat"], r.get("cohort"), r["msg_id"], r["date"], r.get("sender"),
                                 "upi_link" if d == "upi" else "payment_page", anon(url)])
        for vpa in UPI_RE.findall(text):
            if PAY_WORDS.search(text):  # a bare handle@bank alone is too often a username
                pay_rows.append([r["chat"], r.get("cohort"), r["msg_id"], r["date"],
                                 r.get("sender"), "possible_upi_id", anon(vpa.lower())])
    write(os.path.join(args.out, "links.csv"),
          ["chat", "cohort", "msg_id", "date", "sender", "where", "url", "domain", "category"],
          link_rows)
    write(os.path.join(args.out, "domains.csv"),
          ["domain", "category", "links", "messages", "chats", "senders"],
          sorted(([d, categorise(d, codes), s["links"], len(s["msgs"]), len(s["chats"]),
                   len(s["senders"])] for d, s in dom.items()), key=lambda x: -x[2]))
    write(os.path.join(args.out, "payments.csv"),
          ["chat", "cohort", "msg_id", "date", "sender", "kind", "value_hash"], pay_rows)

    # Sender-chat network.
    weights = Counter((r["sender"], r["chat"]) for r in msgs if r.get("sender"))
    nodes = [[c, c, "chat", chats[c][-1].get("cohort") if chats.get(c) else ""]
             for c in sorted(by_chat)]
    nodes += [[s, "", "sender", ""] for s in sorted({s for s, _ in weights})]
    write(os.path.join(args.out, "gephi_nodes.csv"), ["Id", "Label", "kind", "cohort"], nodes)
    write(os.path.join(args.out, "gephi_edges.csv"), ["Source", "Target", "Weight", "Type"],
          [[s, c, w, "Undirected"] for (s, c), w in sorted(weights.items())])


if __name__ == "__main__":
    main()
