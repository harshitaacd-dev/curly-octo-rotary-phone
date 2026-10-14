"""Download NCRB 'Crime in India' tables on crimes against women, cyber crimes
and related topics (human trafficking, sexual offences, crimes against children,
missing persons).

Usage: python scripts/ncrb_download.py 2012 2024 data/ncrb

Scrapes the English 'Contents/Tables' and 'Additional Tables' pages for each
year, keeps tables whose chapter or title matches one of TOPICS, downloads
the Excel version (or the PDF when there is no working Excel link) into
<outdir>/<year>/<topic>/, and writes a catalog.csv describing every file.
"""
import csv, html, os, re, sys, time
from urllib.parse import unquote, urlsplit
import requests

BASE = "https://www.ncrb.gov.in"
PAGES = {
    "main": "/crime-in-india-table-content.html?year={y}",
    "additional": "/crime-in-india-additional-table.html?year={y}&category=",
}
TOPICS = {
    "women": re.compile(r"(?<![a-z])(women|rape|dowry|modesty)(?![a-z])", re.I),
    "cyber": re.compile(r"cyber|\bI\.?\s?T\.? Act\b|information technology", re.I),
    "trafficking": re.compile(r"trafficking|immoral traffic|\bAHT\b", re.I),
    "sexual": re.compile(r"sexual|POCSO", re.I),
    "children": re.compile(r"against children|child(ren)? victims|(?<![a-z])girls?(?![a-z])", re.I),
    "missing": re.compile(r"missing", re.I),
}
# Women-related tables that are about police staffing, not crime.
EXCLUDE = re.compile(r"police strength|strength of|women police|women- police|sanctioned and actual", re.I)
# Site-wide footer/sidebar links that appear on every page.
SITE_FILES = re.compile(r"Internship|Newsletter|AIBE|Training|flyers|ICC-Women|Hackathon|getlatlng|Short_film|CIICover", re.I)


def english_session():
    """NCRB serves Hindi by default and lists fewer files in Hindi; switch to English."""
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (research data download)"
    url = f"{BASE}/crime-in-india-year-wise.html?year=2024&keyword="
    tok = re.search(r'name="csrf-token" content="([^"]+)"', get_page(s, url)).group(1)
    r = s.post(f"{BASE}/api/language/set",
               data={"lang": "en", "slug": "crime-in-india-year-wise", "_csrf": tok},
               headers={"X-Requested-With": "XMLHttpRequest", "X-CSRF-Token": tok,
                        "Referer": url, "Origin": BASE}, timeout=60)
    assert r.json().get("success") == 1, r.text
    return s


def clean(x):
    x = html.unescape(re.sub(r"<[^>]+>", " ", x)).replace("​", "")
    return re.sub(r"\s+", " ", x).strip()


def get_page(s, url):
    for attempt in range(5):
        try:
            r = s.get(url, timeout=120)
            r.raise_for_status()
            return r.text
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(2 ** (attempt + 2))


def list_tables(s, year, page):
    t = get_page(s, BASE + PAGES[page].format(y=year))
    rows = []
    parts = re.split(r'<h2 class="c-genriccontent__subhead">(.*?)</h2>', t, flags=re.S)
    for heading, body in zip(parts[1::2], parts[2::2]):
        for tr in re.findall(r"<tr>(.*?)</tr>", body.split("</table>")[0], re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            links = [l for l in re.findall(r'href="([^"]+)"', tr) if "/uploads/" in l and not SITE_FILES.search(l)]
            if len(tds) < 2 or not links:
                continue
            pdf = next((l for l in links if l.lower().endswith(".pdf")), "")
            xls = next((l for l in links if re.search(r"\.(xlsx?|csv)$", l, re.I)), "")
            rows.append({"year": year, "page": page, "chapter": clean(heading),
                         "title": clean(tds[1]), "pdf": pdf, "excel": xls})
    return rows


def topic_of(row):
    text = f"{row['chapter']} {row['title']}"
    if EXCLUDE.search(text):
        return None
    hits = [k for k, rx in TOPICS.items() if rx.search(text)]
    return "+".join(hits) or None


def safe_name(url):
    name = unquote(os.path.basename(urlsplit(url).path))
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def fetch(s, url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "exists"
    for attempt in range(4):
        try:
            r = s.get(url.replace(" ", "%20"), timeout=180)
            if r.status_code == 200 and r.content and not r.content.lstrip().startswith(b"<"):
                with open(dest, "wb") as f:
                    f.write(r.content)
                return "ok"
            status = f"http {r.status_code}"
            if r.status_code == 404:
                break
        except requests.RequestException as e:
            status = f"error {type(e).__name__}"
        time.sleep(2 ** (attempt + 1))
    return status


def main(y0, y1, outdir):
    s = english_session()
    catalog = []
    for y in range(y0, y1 + 1):
        for page in PAGES:
            for row in list_tables(s, y, page):
                topic = topic_of(row)
                if not topic:
                    continue
                folder = os.path.join(outdir, str(y), topic.split("+")[0])
                os.makedirs(folder, exist_ok=True)
                # Prefer Excel; fall back to the PDF when Excel is missing or its link is broken.
                for url in filter(None, [row["excel"], row["pdf"]]):
                    dest = os.path.join(folder, safe_name(url))
                    status = fetch(s, url, dest)
                    if status in ("ok", "exists"):
                        break
                catalog.append({**row, "topic": topic, "file": os.path.relpath(dest, outdir),
                                "format": os.path.splitext(dest)[1].lstrip(".").lower(), "status": status})
                print(y, page, topic, status, row["title"][:70], file=sys.stderr)
                time.sleep(0.3)
    with open(os.path.join(outdir, "catalog.csv"), "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "topic", "page", "chapter", "title", "format",
                                          "file", "status", "excel", "pdf"])
        w.writeheader()
        w.writerows(catalog)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
