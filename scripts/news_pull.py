"""Pull news headlines about morphed / deepfake sexual images of women in India from Google News RSS.

    python scripts/news_pull.py --out data/external/news            # 2018-01 .. 2024-12
    python scripts/news_pull.py --out data/external/news --start 2025-01 --end 2025-06

One request per query x calendar month. Google News returns at most ~100 items per search, so a
month that comes back full is split into halves (down to ~1 week) until each window fits.
Every response is saved under raw/, so re-running only fetches what is missing. Then build the
dataset with scripts/news_build.py.

Only headlines, outlet, date and link are stored, not article text or images.
"""
import argparse, hashlib, os, random, time, urllib.parse, urllib.request
from datetime import date, timedelta

# (language, query). Kept broad: news_build.py does the filtering. Edit freely.
QUERIES = [
    ("en", "deepfake woman"),
    ("en", "deepfake video actress"),
    ("en", "deepfake obscene arrested"),
    ("en", "morphed photos woman arrested"),
    ("en", "morphed obscene pictures social media"),
    ("en", "morphed images girl police complaint"),
    ("en", "morphing photos blackmail"),
    ("en", "obscene photos women Instagram arrested"),
    ("en", "fake nude photos woman police"),
    ("en", "AI generated obscene images women"),
    ("en", "sextortion morphed video"),
    ("en", "objectionable edited photos woman viral"),
    ("hi", "डीपफेक वीडियो"),
    ("hi", "फोटो मॉर्फ गिरफ्तार"),
    ("hi", "अश्लील फोटो वायरल युवती"),
    ("hi", "आपत्तिजनक फोटो एडिट"),
]
LOCALE = {"en": "hl=en-IN&gl=IN&ceid=IN:en", "hi": "hl=hi&gl=IN&ceid=IN:hi"}
FULL = 95  # a response this size is probably truncated


def month_windows(start, end):
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    while (y, m) <= (ey, em):
        a = date(y, m, 1)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        yield a, date(y, m, 1)  # 'before:' is exclusive


def url_for(lang, q, a, b):
    qq = urllib.parse.quote(f"{q} after:{a - timedelta(days=1)} before:{b}")
    return f"https://news.google.com/rss/search?q={qq}&{LOCALE[lang]}"


def fetch(raw, lang, q, a, b, wait):
    key = hashlib.sha1(f"{lang}|{q}|{a}|{b}".encode()).hexdigest()[:16]
    path = os.path.join(raw, f"{a}_{b}_{lang}_{key}.xml")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    req = urllib.request.Request(url_for(lang, q, a, b), headers={"User-Agent": "Mozilla/5.0 (research)"})
    for attempt in range(6):
        try:
            body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"<!-- lang={lang} query={q} after={a} before={b} -->\n" + body)
            time.sleep(wait + random.uniform(0, wait / 2))
            return body
        except Exception as e:  # 429 / 503 / network
            pause = min(30 * 2 ** attempt, 900)
            print(f"  {type(e).__name__}: {str(e)[:80]} -> waiting {pause}s", flush=True)
            time.sleep(pause)
    raise RuntimeError(f"gave up on {lang} {q} {a}")


def pull(raw, lang, q, a, b, wait):
    body = fetch(raw, lang, q, a, b, wait)
    n = body.count("<item>")
    if n >= FULL and (b - a).days > 8:
        mid = a + (b - a) / 2
        return pull(raw, lang, q, a, mid, wait) + pull(raw, lang, q, mid, b, wait)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/external/news")
    ap.add_argument("--start", default="2018-01")
    ap.add_argument("--end", default="2024-12")
    ap.add_argument("--wait", type=float, default=1.5, help="seconds between requests")
    args = ap.parse_args()
    raw = os.path.join(args.out, "raw")
    os.makedirs(raw, exist_ok=True)
    for a, b in month_windows(args.start, args.end):
        counts = [pull(raw, lang, q, a, b, args.wait) for lang, q in QUERIES]
        print(f"{a:%Y-%m}: {sum(counts)} items  {counts}", flush=True)


if __name__ == "__main__":
    main()
