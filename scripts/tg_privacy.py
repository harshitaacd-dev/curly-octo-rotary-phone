"""Pseudonymisation and retention rules shared by the Telegram scripts.

Everything that can identify a person is replaced by a salted HMAC before it is written:
user, chat and forwarded-from ids, admin signatures, forwarded-from names, chat titles and
usernames, and, inside message text and links, phone numbers, email addresses, UPI IDs,
ID-card-like numbers, @mentions and the path of every non-Telegram URL (a victim's
instagram.com/<handle> becomes [URL instagram.com #3f9c...]). The same value always gets
the same hash, so repeats can still be counted.

Kept in clear, as approved for finding further groups: Telegram links (t.me/...), and bot
usernames (@...bot), which are tools rather than people. Personal names written in free
text cannot be found by pattern and stay in the text.

Data may only be kept until DELETE_AFTER (the submission date); the scripts refuse to run
after it, and tg_purge.py deletes everything.
"""
import hashlib, hmac, os, re, sys
from datetime import date
from urllib.parse import urlsplit

DELETE_AFTER = date(2026, 11, 19)
SALT = os.environ.get("TG_SALT", "").encode()

TELEGRAM_HOSTS = {"t.me", "telegram.me", "telegram.dog"}


def check_ready():
    if date.today() > DELETE_AFTER:
        sys.exit(f"The retention period ended on {DELETE_AFTER}. Run scripts/tg_purge.py to "
                 "delete the data; nothing more may be collected or analysed.")
    if len(SALT) < 16:
        sys.exit("Set TG_SALT to a random string of at least 16 characters (the same one every run).")


def anon(value, kind=""):
    """Salted HMAC, 16 hex characters; None and "" stay None."""
    if value is None or value == "":
        return None
    return hmac.new(SALT, f"{kind}:{value}".encode(), hashlib.sha256).hexdigest()[:16]


def is_bot_name(name):
    return bool(name) and name.lower().rstrip("/").endswith("bot")


# ---------------------------------------------------------------- links
def split_url(url):
    """(host, path+query) of a URL that may lack a scheme."""
    if url.lower().startswith("upi://"):
        return "upi", url[6:]
    parts = urlsplit(url if "://" in url else "http://" + url)
    host = (parts.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    rest = parts.path.strip("/") + (("?" + parts.query) if parts.query else "")
    return host, rest


def link_record(url, where):
    """What is stored about one link: domain always; full URL only for Telegram."""
    host, rest = split_url(url)
    rec = {"where": where, "domain": host, "path_hash": anon(rest.lower(), "path") if rest else None}
    if host in TELEGRAM_HOSTS:
        rec["telegram"] = f"{host}/{rest}"
        rec["bot"] = rest.split("?")[0] if is_bot_name(rest.split("?")[0]) else None
    if host == "upi":
        rec["upi_hash"] = anon(re.sub(r"^pay\?pa=([^&]+).*", r"\1", rest).lower(), "upi")
    return rec


def url_token(url):
    host, rest = split_url(url)
    if host in TELEGRAM_HOSTS:
        return url
    if host == "upi":
        return f"[UPI #{link_record(url, '')['upi_hash']}]"
    return f"[URL {host} #{anon(rest.lower(), 'path')}]" if rest else f"[URL {host}]"


# ---------------------------------------------------------------- text
URL_RE = re.compile(r"(?:https?://|www\.|upi://)[^\s<>\"'\]\)]+"
                    r"|\b(?:t\.me|telegram\.me|wa\.me)/[^\s<>\"'\]\)]+", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
# Virtual payment address: handle@bank, with no dot after the bank part (unlike an email).
UPI_RE = re.compile(r"(?<![\w.@])[\w.\-]{2,64}@[a-z]{2,20}(?![\w.@])", re.I)
MENTION_RE = re.compile(r"(?<![\w@])@([A-Za-z][\w]{3,31})")
# Indian mobile numbers (optional +91 / 0091 / 0 prefix), or any number written with a leading +.
PHONE_RE = re.compile(r"(?<![\d+])(?:(?:\+|00)?91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)"
                      r"|(?<![\d+])\+\d[\d\s-]{8,15}\d(?!\d)")
ID12_RE = re.compile(r"(?<!\d)\d{4}[\s-]\d{4}[\s-]\d{4}(?!\d)")  # Aadhaar-style


def _digits(s):
    return re.sub(r"\D", "", s)


def pseudonymise(text):
    """Return (text with identifiers replaced by tokens, counts per identifier type)."""
    counts = {"url": 0, "email": 0, "upi": 0, "mention": 0, "phone": 0, "id_number": 0}
    if not text:
        return text or "", counts

    def sub(rx, fn, kind):
        nonlocal text

        def repl(m):
            out = fn(m)
            if out != m.group(0):
                counts[kind] += 1
            return out
        text = rx.sub(repl, text)

    def url(m):
        u = m.group(0)
        core = u.rstrip(".,;:!?")
        return url_token(core) + u[len(core):]

    # URLs first so their paths are not mistaken for phone numbers or mentions.
    sub(URL_RE, url, "url")
    sub(EMAIL_RE, lambda m: f"[EMAIL #{anon(m.group(0).lower(), 'email')}]", "email")
    sub(UPI_RE, lambda m: f"[UPI #{anon(m.group(0).lower(), 'upi')}]", "upi")
    sub(MENTION_RE, lambda m: m.group(0) if is_bot_name(m.group(1))
        else f"[USER #{anon(m.group(1).lower(), 'user')}]", "mention")
    sub(ID12_RE, lambda m: f"[ID #{anon(_digits(m.group(0)), 'id')}]", "id_number")
    sub(PHONE_RE, lambda m: f"[PHONE #{anon(_digits(m.group(0))[-10:], 'phone')}]", "phone")
    return text, counts
