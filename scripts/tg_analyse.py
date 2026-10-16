"""Code, count and date the Telegram collection: practices, morphed media, monthly series.

Usage: python scripts/tg_analyse.py data/telegram data/telegram/out
           [--lexicon analysis/telegram/lexicon.csv] [--codes coded_domains.csv] [--sample 50]

Reads <in>/messages.jsonl and <in>/chats.jsonl from scripts/tg_collect.py (already
pseudonymised), keeps the latest snapshot of each message, and writes to <out>:

  messages_coded.csv   one row per message, no text: date, month, language, practices
                       matched (lexicon.csv, AI Forensics Table 3 categories), morphed-media
                       flag and which signal set it, uploader/requester role, media, bots
  monthly.csv          the time series: per month, for all chats, per cohort and per
                       language: messages, active and new senders, media, morphed-media
                       messages and senders, each practice, and how many chats were
                       observable (their oldest surviving message is on or before that month)
  chat_summary.csv     per chat: size, status, creation date, oldest surviving message,
                       messages, senders, media, edits, deletions, renames
  bots.csv             every bot used or linked: messages, chats, months, nudify-like name
  links.csv, domains.csv   links by domain and platform category (paths hashed)
  snowball_leads.csv   Telegram links in clear, for finding further groups. Working file:
                       stays local and is deleted with the rest
  payments.csv         UPI IDs, upi:// links and payment pages (hashes only)
  cohort_overlap.csv, chat_overlap.csv   shared senders and media
  gephi_nodes.csv, gephi_edges.csv       sender-chat network
  validation_sample.csv  --sample N random matches per practice, with (pseudonymised)
                       text, for hand-checking how precise each keyword set is

Morphed media is never seen (media is not downloaded), so a message counts as morphed
media when any of these holds: its text matches the `deepfake` practice; it was sent
through, or by, or links to a bot whose name looks like a nudify / face-swap tool; or it
links to a site in the "NCII AI Image & Video Generator" category.
"""
import argparse, csv, json, os, random, re, sys
from collections import Counter, defaultdict
from itertools import combinations

sys.path.insert(0, os.path.dirname(__file__))
from tg_privacy import check_ready, is_bot_name  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEXICON = os.path.join(HERE, "..", "analysis", "telegram", "lexicon.csv")

# Bot usernames and domains that look like nudify / face-swap / deepfake tools.
NUDIFY_RE = re.compile(r"nudi|nude|naked|undres|clothoff|cloth|deepnude|deepfake|faceswap|"
                       r"face_?swap|xray|x_ray|strip|nsfw|pornify|soulgen|desnud|denud|nangi", re.I)

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
    "Payment": ["upi", "paypal.me", "paypal.com", "razorpay.me", "rzp.io", "pages.razorpay.com",
                "instamojo.com", "paytm.me", "p.paytm.me", "cosmofeed.com", "superprofile.bio",
                "buymeacoffee.com", "ko-fi.com", "patreon.com"],
    "NCII AI Image & Video Generator": ["clothoff.io", "clothoff.net", "undress.app",
                                        "undress.ai", "nudify.online", "deepnude.cc",
                                        "soulgen.net", "pornpen.ai", "pornify.cc"],
    "Search Engine": ["google.com", "bing.com", "duckduckgo.com"],
    "Government Site": ["gov.in", "nic.in"],
}
DOMAIN_CATEGORY = {d: c for c, ds in CATEGORIES.items() for d in ds}
AI_GEN = "NCII AI Image & Video Generator"

# Language by script; Latin text split into Hinglish / Romanised Bangla / other.
SCRIPTS = [("meitei", r"[ꯀ-꯿]"), ("bangla", r"[ঀ-৿]"),
           ("tamil", r"[஀-௿]"), ("hindi", r"[ऀ-ॿ]"),
           ("telugu", r"[ఀ-౿]"), ("kannada", r"[ಀ-೿]"),
           ("malayalam", r"[ഀ-ൿ]"), ("gujarati", r"[઀-૿]"),
           ("punjabi", r"[਀-੿]"), ("odia", r"[଀-୿]"),
           ("latin", r"[A-Za-z]")]
SCRIPTS = [(n, re.compile(p)) for n, p in SCRIPTS]
# Word lists from is_hinglish in scripts/build_threat_corpus.py (text_threats branch).
HI_WORDS = set("""hai hain hn nahi nahin nhi na kya kyu kyun kyon ko ki ke ka se mein mai
tu tum tera teri tere mera meri mere aur bhi toh ye yeh wo woh vo kar karo karna karte
kiya raha rahi rhe gaya gayi diya dunga denge sala saala saali bhai behen bhen maa
ladki ladkiyon aurat randi chutiya kutta kutti jaise sab kuch bahut bohot abhi kab
kaise apni apna apne unka uska iska isko usko wala wali wale hoga hogi chahiye lekin
jab tab agar hum humko tujhe tujhko mujhe mujhko sabko unko inko yaar ji""".split())
BN_WORDS = set("""ami tumi tor tui kore korte kori koro hobe ache achhe ar er oi ei
amar tomar oder ora bou keno""".split())
TOKEN_RE = re.compile(r"\[(?:URL|UPI|EMAIL|USER|PHONE|ID)[^\]]*\]")


def language(text):
    text = TOKEN_RE.sub(" ", text or "")
    counts = [(len(rx.findall(text)), name) for name, rx in SCRIPTS]
    n, name = max(counts)
    if n == 0:
        return "none"
    if name != "latin":
        return name
    toks = re.findall(r"[a-z]+", text.lower())
    hi, bn = sum(t in HI_WORDS for t in toks), sum(t in BN_WORDS for t in toks)
    need = 1 if len(toks) <= 4 else 2
    if hi >= need and hi > bn:
        return "hinglish"
    if bn >= need:
        return "bangla_roman"
    return "english"


def load_lexicon(path):
    lex = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lex[r["practice"]].append(re.compile(r["pattern"], re.I))
    return {p: re.compile("|".join(f"(?:{rx.pattern})" for rx in rxs), re.I) for p, rxs in lex.items()}


def categorise(domain, codes):
    parts = domain.split(".")
    for i in range(len(parts)):  # most specific suffix first: pages.razorpay.com, gov.in
        suffix = ".".join(parts[i:])
        if suffix in codes:
            return codes[suffix]
        if suffix in DOMAIN_CATEGORY:
            return DOMAIN_CATEGORY[suffix]
    return AI_GEN if NUDIFY_RE.search(domain) else "uncoded"


def load(path):
    if not os.path.exists(path):
        return []
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


def bots_of(r):
    """Bot usernames tied to a message: sent by, via, mentioned or linked."""
    out = {b for b in (r.get("sender_bot"), r.get("via_bot")) if b}
    out |= {m.lower() for m in re.findall(r"@(\w+bot)\b", r.get("text") or "", re.I)}
    out |= {l["bot"] for l in r.get("links") or [] if l.get("bot")}
    return {b.lower() for b in out}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--lexicon", default=DEFAULT_LEXICON)
    ap.add_argument("--codes", help="CSV with domain,category for hand-coded domains")
    ap.add_argument("--sample", type=int, default=50, help="validation rows per practice")
    args = ap.parse_args()
    check_ready()
    codes = {}
    if args.codes:
        with open(args.codes, encoding="utf-8") as f:
            codes = {r["domain"].strip().lower(): r["category"].strip() for r in csv.DictReader(f)}
    lex = load_lexicon(args.lexicon)
    practices = sorted(p for p in lex if not p.startswith("role_"))
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
    msgs = sorted((r for r in latest.values() if "date" in r), key=lambda r: r["date"])
    chats = defaultdict(list)
    for r in load(os.path.join(args.src, "chats.jsonl")):
        chats[r["chat"]].append(r)

    # ------------------------------------------------------------ code each message
    for r in msgs:
        text = r.get("text") or ""
        r["month"] = r["date"][:7]
        r["lang"] = language(text)
        r["practices"] = {p for p, rx in lex.items() if rx.search(text)}
        cats = {categorise(l["domain"], codes) for l in r.get("links") or []}
        r["bots"] = bots_of(r)
        signals = []
        if "deepfake" in r["practices"]:
            signals.append("text")
        if any(NUDIFY_RE.search(b) for b in r["bots"]):
            signals.append("nudify_bot")
        if AI_GEN in cats:
            signals.append("ai_generator_link")
        r["morph_signals"] = signals
        r["role"] = "+".join(x for x in ("uploader", "requester") if f"role_{x}" in r["practices"])

    write(os.path.join(args.out, "messages_coded.csv"),
          ["chat", "cohort", "msg_id", "date", "month", "fwd_date", "sender", "sender_bot",
           "via_bot", "lang", "practices", "morph", "morph_signals", "role", "media_kind",
           "media_key", "deleted"],
          [[r["chat"], r.get("cohort"), r["msg_id"], r["date"], r["month"], r.get("fwd_date"),
            r.get("sender"), r.get("sender_bot"), r.get("via_bot"), r["lang"],
            ";".join(sorted(p for p in r["practices"] if not p.startswith("role_"))),
            int(bool(r["morph_signals"])), ";".join(r["morph_signals"]), r["role"],
            r.get("media_kind"), r.get("media_key"), int(bool(r.get("deleted"))),
            ] for r in msgs])

    # ------------------------------------------------------------ monthly series
    oldest = {}
    for alias, snaps in chats.items():
        dates = [s["oldest_message_date"] for s in snaps if s.get("oldest_message_date")]
        if dates:
            oldest[alias] = min(dates)[:7]
    for r in msgs:  # fall back to the earliest collected message
        if r["chat"] not in oldest or r["month"] < oldest[r["chat"]]:
            oldest[r["chat"]] = r["month"]
    chat_cohort = {r["chat"]: r.get("cohort") or "-" for r in msgs}
    first_seen = {}
    for r in msgs:
        if r.get("sender"):
            first_seen.setdefault(r["sender"], r["month"])

    groups = defaultdict(list)  # (dimension, value, month) -> messages
    for r in msgs:
        for dim, val in (("all", "all"), ("cohort", r.get("cohort") or "-"), ("language", r["lang"])):
            groups[(dim, val, r["month"])].append(r)
    rows = []
    for (dim, val, month), ms in sorted(groups.items()):
        observable = [c for c, m in oldest.items() if m <= month
                      and (dim != "cohort" or chat_cohort.get(c) == val)]
        senders = {r["sender"] for r in ms if r.get("sender")}
        morph = [r for r in ms if r["morph_signals"]]
        rows.append([month, dim, val, len(observable), len(ms), len(senders),
                     sum(1 for s in senders if first_seen[s] == month),
                     sum(1 for r in ms if r.get("media_key")),
                     len({r["media_key"] for r in ms if r.get("media_key")}),
                     sum(1 for r in ms if r.get("fwd_date")),
                     len(morph), len({r["sender"] for r in morph if r.get("sender")}),
                     sum(1 for r in morph if "text" in r["morph_signals"]),
                     sum(1 for r in morph if "nudify_bot" in r["morph_signals"]),
                     sum(1 for r in morph if "ai_generator_link" in r["morph_signals"])]
                    + [sum(1 for r in ms if p in r["practices"]) for p in practices])
    write(os.path.join(args.out, "monthly.csv"),
          ["month", "dimension", "group", "chats_observable", "messages", "active_senders",
           "new_senders", "media_messages", "distinct_media", "forwards", "morph_messages",
           "morph_senders", "morph_by_text", "morph_by_nudify_bot", "morph_by_ai_generator_link"]
          + [f"n_{p}" for p in practices], rows)

    # ------------------------------------------------------------ chats
    by_chat = defaultdict(list)
    sender_sets, media_sets = defaultdict(set), defaultdict(set)
    cohort_senders, cohort_media, media_chats = defaultdict(set), defaultdict(set), defaultdict(set)
    for r in msgs:
        by_chat[r["chat"]].append(r)
        co = r.get("cohort") or "-"
        if r.get("sender"):
            sender_sets[r["chat"]].add(r["sender"])
            cohort_senders[co].add(r["sender"])
        if r.get("media_key"):
            media_sets[r["chat"]].add(r["media_key"])
            cohort_media[co].add(r["media_key"])
            media_chats[r["media_key"]].add(r["chat"])
    rows = []
    for alias in sorted(set(by_chat) | set(chats)):
        ms, snaps = by_chat.get(alias, []), chats.get(alias, [])
        last = snaps[-1] if snaps else {}
        titles = [s.get("title_hash") for s in snaps if s.get("title_hash")]
        created = next((s["created_date"] for s in snaps if s.get("created_date")), "")
        rows.append([alias, last.get("cohort"), last.get("type"), last.get("status"),
                     last.get("members"), created[:10], oldest.get(alias, ""),
                     len(ms), len(sender_sets[alias]),
                     sum(1 for r in ms if r.get("media_key")), len(media_sets[alias]),
                     sum(1 for k in media_sets[alias] if len(media_chats[k]) > 1),
                     sum(1 for r in ms if r["morph_signals"]),
                     edits[alias], deleted[alias],
                     sum(1 for a, b in zip(titles, titles[1:]) if a != b),
                     ms[0]["date"][:10] if ms else "", ms[-1]["date"][:10] if ms else ""])
    write(os.path.join(args.out, "chat_summary.csv"),
          ["chat", "cohort", "type", "last_status", "members", "created", "oldest_month",
           "messages", "active_senders", "media_messages", "distinct_media",
           "media_also_elsewhere", "morph_messages", "edits_seen", "deletions_seen",
           "title_changes", "first_collected", "last_collected"], rows)

    shared = sum(1 for cs in media_chats.values() if len(cs) > 1)
    print(f"{len(msgs)} messages, {len(set().union(*sender_sets.values())) if sender_sets else 0}"
          f" active senders, {len(media_chats)} distinct media ({shared} in more than one chat), "
          f"{sum(1 for r in msgs if r['morph_signals'])} morphed-media messages")

    head = ["a", "b", "senders_a", "senders_b", "shared_senders", "media_a", "media_b",
            "shared_media", "share_of_a_media", "share_of_b_media"]
    write(os.path.join(args.out, "cohort_overlap.csv"), head,
          overlap_rows(cohort_senders.keys() | cohort_media.keys(), cohort_senders, cohort_media))
    write(os.path.join(args.out, "chat_overlap.csv"), head,
          overlap_rows(sender_sets.keys() | media_sets.keys(), sender_sets, media_sets))

    # ------------------------------------------------------------ bots
    bot = defaultdict(lambda: {"msgs": 0, "chats": set(), "months": set(), "senders": set()})
    for r in msgs:
        for b in r["bots"]:
            s = bot[b]
            s["msgs"] += 1
            s["chats"].add(r["chat"])
            s["months"].add(r["month"])
            if r.get("sender"):
                s["senders"].add(r["sender"])
    write(os.path.join(args.out, "bots.csv"),
          ["bot", "nudify_like_name", "messages", "chats", "senders", "first_month", "last_month"],
          sorted(([b, int(bool(NUDIFY_RE.search(b))), s["msgs"], len(s["chats"]), len(s["senders"]),
                   min(s["months"]), max(s["months"])] for b, s in bot.items()), key=lambda x: -x[2]))

    # ------------------------------------------------------------ links and payments
    link_rows, pay_rows, leads = [], [], defaultdict(lambda: {"n": 0, "chats": set(), "first": None})
    dom = defaultdict(lambda: {"links": 0, "msgs": set(), "chats": set(), "senders": set()})
    for r in msgs:
        for l in r.get("links") or []:
            d, cat = l["domain"], categorise(l["domain"], codes)
            tg = l.get("telegram")
            shown = (tg if tg and (l.get("bot")) else
                     f"{d}/#{l['path_hash']}" if l.get("path_hash") else d)
            link_rows.append([r["chat"], r.get("cohort"), r["msg_id"], r["date"], r.get("sender"),
                              l["where"], shown, d, cat])
            s = dom[d]
            s["links"] += 1
            s["msgs"].add((r["chat"], r["msg_id"]))
            s["chats"].add(r["chat"])
            if r.get("sender"):
                s["senders"].add(r["sender"])
            if tg:
                lead = leads[tg]
                lead["n"] += 1
                lead["chats"].add(r["chat"])
                lead["first"] = min(filter(None, [lead["first"], r["date"][:10]]))
            if cat == "Payment":
                pay_rows.append([r["chat"], r.get("cohort"), r["msg_id"], r["date"], r.get("sender"),
                                 "upi_link" if d == "upi" else "payment_page",
                                 l.get("upi_hash") or l.get("path_hash") or d])
        for h in re.findall(r"\[UPI #(\w+)\]", r.get("text") or ""):
            pay_rows.append([r["chat"], r.get("cohort"), r["msg_id"], r["date"], r.get("sender"),
                             "upi_id", h])
    write(os.path.join(args.out, "links.csv"),
          ["chat", "cohort", "msg_id", "date", "sender", "where", "link", "domain", "category"],
          link_rows)
    write(os.path.join(args.out, "domains.csv"),
          ["domain", "category", "links", "messages", "chats", "senders"],
          sorted(([d, categorise(d, codes), s["links"], len(s["msgs"]), len(s["chats"]),
                   len(s["senders"])] for d, s in dom.items()), key=lambda x: -x[2]))
    write(os.path.join(args.out, "snowball_leads.csv"),
          ["telegram_link", "is_bot", "mentions", "chats", "first_seen"],
          sorted(([t, int(is_bot_name(t.split("/", 1)[-1].split("?")[0])), s["n"], len(s["chats"]),
                   s["first"]] for t, s in leads.items()), key=lambda x: -x[2]))
    write(os.path.join(args.out, "payments.csv"),
          ["chat", "cohort", "msg_id", "date", "sender", "kind", "value_hash"], pay_rows)

    # ------------------------------------------------------------ validation sample
    rng, rows = random.Random(1), []
    for p in sorted(lex):
        hits = [r for r in msgs if p in r["practices"]]
        for r in rng.sample(hits, min(args.sample, len(hits))):
            rows.append([p, r["chat"], r["msg_id"], r["date"][:10], r["lang"],
                         (r.get("text") or "")[:500], ""])
    write(os.path.join(args.out, "validation_sample.csv"),
          ["practice", "chat", "msg_id", "date", "lang", "text", "correct (1/0)"], rows)

    # ------------------------------------------------------------ network
    weights = Counter((r["sender"], r["chat"]) for r in msgs if r.get("sender"))
    nodes = [[c, c, "chat", chat_cohort.get(c, "")] for c in sorted(by_chat)]
    nodes += [[s, "", "sender", ""] for s in sorted({s for s, _ in weights})]
    write(os.path.join(args.out, "gephi_nodes.csv"), ["Id", "Label", "kind", "cohort"], nodes)
    write(os.path.join(args.out, "gephi_edges.csv"), ["Source", "Target", "Weight", "Type"],
          [[s, c, w, "Undirected"] for (s, c), w in sorted(weights.items())])


if __name__ == "__main__":
    main()
