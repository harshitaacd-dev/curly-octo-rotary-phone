"""Screen candidate chats from tg_find.py one at a time, then build the chat list.

Usage:
  python scripts/tg_screen.py data/telegram/candidates.csv          screen undecided rows
  python scripts/tg_screen.py data/telegram/candidates.csv --redo   go through all rows again
  python scripts/tg_screen.py data/telegram/candidates.csv --build telegram_chats.json
                                                                     add included chats to the list

Shows the title, description, size, creation date and the search terms that found each
chat, with a suggestion from keyword matches (lexicon.csv practices, signs of payment or
share-to-join gates). The suggestion is a hint only: you decide. Nothing is opened or
joined. Each decision is saved to the CSV straight away, with the cohort, an optional
note and the time, so you can stop with q (or Ctrl+C) and carry on later.

Keys:  i include   c exclude-commercial   x exclude-irrelevant
       p gated-payment   s gated-share   b bot-nudify   o bot-other
       Enter = take the suggestion   k skip for now   u undo last   q quit
       A note can follow the key on the same line, e.g.  x not Indian
"""
import argparse, csv, json, os, re, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from tg_find import FIELDS, norm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LEXICON = os.path.join(HERE, "..", "analysis", "telegram", "lexicon.csv")

KEYS = {"i": "include", "c": "exclude-commercial", "x": "exclude-irrelevant",
        "p": "gated-payment", "s": "gated-share", "b": "bot-nudify", "o": "bot-other"}
# Practices that point to non-consensual content, in the order they are shown.
SIGNAL = ["deepfake", "ncii", "spycam", "tribute", "doxxing", "targeted", "rape", "sexist_hate",
          "archive", "hacking", "spyware", "roleplay"]
PAY_RE = re.compile(r"\b(?:paid|payment|pay|price|subscri\w*|premium|vip|upi|paytm|g ?pay|"
                    r"phone ?pe|demo|lifetime|rs\.?\s?\d+|inr|₹)|₹", re.I)
SHARE_RE = re.compile(r"\bshare (?:this|the|link|karo|kro)\b|\b(?:add|invite) \d+\b|"
                      r"\bshare (?:in|to|with) \d+\b|\bunlock\b", re.I)
COMMERCIAL_RE = re.compile(r"\bonly ?fans\b|\bof ?model\b|\bcam ?girl\b|\bpornstar\b|\bmy (?:own )?content\b|"
                           r"\bverified creator\b|\bfansly\b", re.I)
NUDIFY_RE = re.compile(r"nudi|nude|naked|undres|cloth|deepnude|deepfake|faceswap|face_?swap|"
                       r"xray|strip|nsfw|nangi", re.I)
PREFIX = {"hindi": "HI", "hinglish": "HG", "bangla": "BN", "tamil": "TA", "meitei": "MN",
          "english": "EN"}


def load_lexicon():
    pats = {}
    with open(LEXICON, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pats.setdefault(r["practice"], []).append(r["pattern"])
    return {p: re.compile("|".join(f"(?:{x})" for x in v), re.I) for p, v in pats.items()}


def suggest(row, lex):
    """(suggested decision, reasons) from the title, description and username."""
    text = " ".join([row["title"], row["description"], row["link"]])
    hits = [p for p in SIGNAL if p in lex and lex[p].search(text)]
    reasons = list(hits)
    if row["kind"] == "bot":
        return ("bot-nudify" if NUDIFY_RE.search(row["link"]) else "bot-other"), reasons
    if SHARE_RE.search(text):
        return "gated-share", reasons + ["share-to-join"]
    if PAY_RE.search(text):
        reasons.append("payment")
    if COMMERCIAL_RE.search(text) and not hits:
        return "exclude-commercial", reasons + ["creator/commercial"]
    if hits:
        return ("gated-payment" if "payment" in reasons else "include"), reasons
    return "", reasons


def save(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def show(i, n, row, hint, reasons):
    print("\n" + "─" * 72)
    print(f"[{i}/{n}]  {row['kind'].upper()}   {row['link']}")
    print(f"members: {row['members'] or '?'}   created: {row['created'] or '?'}   "
          f"found by: {row['found_by']}   cohorts: {row['cohorts'] or '-'}")
    flags = [k for k in ("verified", "scam", "fake", "restricted") if row.get(k) == "1"]
    if flags:
        print("flags:", ", ".join(flags))
    print(f"title: {row['title']}")
    if row["description"]:
        print(f"description: {row['description']}")
    if row["in_chat_list"] == "1":
        print("(already in your chat list)")
    print(f"suggestion: {hint or 'none'}" + (f"  ({', '.join(reasons)})" if reasons else ""))


def screen(path, redo):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in FIELDS:
            r.setdefault(k, "")
    todo = [r for r in rows if redo or not r["decision"]]
    lex = load_lexicon()
    print(__doc__.split("Keys:")[1].strip())
    print(f"\n{len(todo)} to screen ({len(rows)} candidates in total).")
    history, i = [], 0
    while i < len(todo):
        row = todo[i]
        hint, reasons = suggest(row, lex)
        show(i + 1, len(todo), row, hint, reasons)
        try:
            entry = input("decision [i/c/x/p/s/b/o (+ note), Enter = suggestion, k/u/q]: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        key, _, note = entry.partition(" ")
        key = key.lower()
        if key == "q":
            break
        if key == "u":
            if history:
                i = history.pop()
                todo[i]["decision"] = todo[i]["screened_at"] = ""
                save(path, rows)
            continue
        if key == "k":
            i += 1
            continue
        decision = KEYS.get(key) or (hint if key == "" else None)
        if not decision:
            print("Not a valid key.")
            continue
        if decision == "include":
            default = (row["cohort"] or row["cohorts"].split(";")[0]).strip()
            try:
                cohort = input(f"cohort [{default or 'type one'}]: ").strip().lower() or default
            except (EOFError, KeyboardInterrupt):
                break
            row["cohort"] = cohort
        row["note"] = note.strip() or row["note"]
        row["decision"] = decision
        row["screened_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        save(path, rows)
        history.append(i)
        i += 1
    done = sum(1 for r in rows if r["decision"])
    inc = sum(1 for r in rows if r["decision"] == "include")
    print(f"\nSaved. {done}/{len(rows)} decided, {inc} included.")


def build(path, chats_path):
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["decision"] == "include" and r["kind"] != "bot"]
    chats = {"chats": []}
    if os.path.exists(chats_path):
        with open(chats_path, encoding="utf-8") as f:
            chats = json.load(f)
    have = {norm(str(c["chat"])) for c in chats["chats"]}
    used = {c["alias"] for c in chats["chats"]}
    added = 0
    for r in rows:
        if norm(r["link"]) in have:
            continue
        cohort = r.get("cohort") or (r["cohorts"].split(";")[0] if r["cohorts"] else "other")
        prefix = PREFIX.get(cohort, cohort[:2].upper() or "XX")
        n = 1
        while f"{prefix}-{n:02d}" in used:
            n += 1
        alias = f"{prefix}-{n:02d}"
        used.add(alias)
        chats["chats"].append({"alias": alias, "cohort": cohort, "chat": "https://" + r["link"]})
        added += 1
    with open(chats_path, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)
    print(f"Added {added} chats to {chats_path} ({len(chats['chats'])} in total). "
          "Join each one by hand in the Telegram app before collecting.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("candidates")
    ap.add_argument("--redo", action="store_true", help="screen rows that already have a decision")
    ap.add_argument("--build", metavar="CHATS_JSON", help="add included chats to this chat list")
    args = ap.parse_args()
    if args.build:
        build(args.candidates, args.build)
    else:
        screen(args.candidates, args.redo)


if __name__ == "__main__":
    main()
