"""Build an incident dataset of morphed / deepfake sexual images of women in India from news headlines.

    python scripts/news_build.py data/external/news data/clean

Reads the Google News responses saved by news_pull.py and writes, under the output folder:
    news_articles.csv        one row per unique headline pulled, with the classification flags
    news_incidents.csv       in-scope articles grouped into incidents (one row per incident)
    news_incidents_state_year.csv   incident counts by State/UT x year x image type
    news_validation_sample.csv      random in-scope + out-of-scope headlines to hand-label

Everything is rule-based on the headline (no article text), so it is transparent and re-runnable;
check precision with the validation sample before relying on the numbers. Victim names are not
extracted. Public-figure names are used only to group coverage of the same case.
"""
import argparse, glob, os, re, sys, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from india_places import FOREIGN, FOREIGN_OUTLETS, STATES  # noqa: E402

DEV = r"ऀ-ॿ"  # Devanagari block


def rx(words):
    """Regex matching any of the words, with word boundaries that also work for Hindi."""
    alt = "|".join(sorted(words, key=len, reverse=True))
    return re.compile(rf"(?<![\w{DEV}])(?:{alt})(?![{DEV}])", re.I)


AI = rx([r"deep\s?-?fakes?\w*", r"ai", r"a\.i\.", "artificial intelligence", r"face\s?-?swap\w*", r"nudif\w*",
         r"undress(?:ing)? app\w*", r"ai-generated", r"ai generated", "generative", r"डीप\s?फेक", "एआई",
         "आर्टिफिशियल इंटेलिजेंस"])
MORPH = rx([r"morph\w*", r"edited", r"photoshop\w*", r"doctored", r"manipulated",
            r"fake (?:nude|obscene|porn\w*|photos?|pictures?|pics?|images?|videos?|profiles?)",
            r"मॉर्फ\w*", r"मार्फ\w*", r"मॉर्फिंग", r"एडिट\w*", r"फर्जी (?:फोटो|तस्वीर\w*|वीडियो|आईडी)",
            r"फेक (?:फोटो|आईडी|प्रोफाइल|वीडियो)", r"छेड़छाड़ कर", r"चेहरा लगा\w*", r"फोटो लगा\w*"])
SEXUAL = rx([r"obscen\w*", r"nudes?", r"nudity", r"naked", r"porn\w*", r"explicit", r"vulgar", r"objectionable",
             r"intimate", r"sexual\w*", r"lewd", r"indecent", r"sextortion", r"private (?:photos?|pictures?|videos?)",
             r"compromising", r"semi-nude", r"अश्लील", r"आपत्तिजनक", r"न्यूड", r"नग्न", r"पोर्न\w*", r"गंदी",
             r"सेक्सटॉर्शन", r"निजी (?:फोटो|तस्वीर\w*|वीडियो)", r"अर्धनग्न"])
MEDIA = rx([r"photos?", r"pics?", r"pictures?", r"images?", r"videos?", r"clips?", r"selfies?", r"snaps?",
            r"फोटो\w*", r"तस्वीर\w*", r"वीडियो", r"फ़ोटो", r"चित्र"])
FEMALE = rx([r"wom[ae]n", r"girls?", r"actress\w*", r"female", r"wife", r"girlfriend", r"lady", r"ladies",
             r"daughters?", r"sisters?", r"mother", r"schoolgirls?", r"her", r"she", r"minor", r"teen\w*",
             r"students?", r"colleagues?", r"classmates?", r"influencer", r"महिला\w*", r"युवती\w*", r"लड़की\w*",
             r"लड़कियों", r"छात्रा\w*", r"अभिनेत्री", r"एक्ट्रेस", r"पत्नी", r"बेटी", r"बहन", r"प्रेमिका",
             r"नाबालिग", r"किशोरी", r"सहेली", r"भाभी", r"शिक्षिका", r"बहू", r"दुल्हन", r"नर्स", r"मॉडल"])
MINOR = rx([r"minors?", r"schoolgirls?", r"girl students?", r"class \d+", r"teen\w*", r"नाबालिग", r"किशोरी",
            r"छात्रा\w*", r"स्कूली"])
POLICE = rx([r"arrest\w*", r"held", r"nabbed", r"booked", r"fir", r"case registered", r"cases? (?:filed|lodged)",
             r"complaints?", r"detained", r"police", r"cops?", r"cyber (?:cell|police|crime)", r"chargesheet\w*",
             r"convict\w*", r"sentenced", r"jail\w*", r"bail", r"probe", r"accused", r"court",
             r"गिरफ्तार\w*", r"मामला दर्ज", r"केस दर्ज", r"एफआईआर", r"मुकदमा\w*", r"पुलिस", r"शिकायत",
             r"हिरासत", r"जेल", r"सजा", r"दबोच\w*", r"आरोपी", r"धराया", r"पकड़ा\w*", r"साइबर थाना",
             r"रिपोर्ट दर्ज", r"कोर्ट", r"अदालत"])
VIRAL = rx([r"viral", r"surfaces?", r"circulat\w*", r"victims?", r"falls? prey", r"targeted", r"leaked?",
            r"shared", r"uploaded", r"posted", r"वायरल", r"शिकार", r"लीक", r"अपलोड", r"शेयर", r"पोस्ट"])
BLACKMAIL = rx([r"blackmail\w*", r"extort\w*", r"sextortion", r"threat\w*", r"ब्लैकमेल\w*", r"धमकी", r"वसूली",
                r"सेक्सटॉर्शन"])
SUICIDE = rx([r"suicide", r"ends? (?:her )?life", r"आत्महत्या", r"खुदकुशी", r"सुसाइड"])
EXPLAINER = rx([r"how to", r"explained", r"explainer", r"what is", r"what are", r"tips", r"ways to", r"guide",
                r"opinion", r"column", r"podcast", r"webinar", r"quiz", r"क्या (?:है|होता|होती)", r"कैसे पहचान\w*",
                r"कैसे बचें", r"जानिए", r"जानें", r"टिप्स", r"fact check", r"फैक्ट चेक"])
POLICY = rx([r"ministers?", r"ministry", r"govt", r"government", r"centre", r"meity", r"it rules", r"advisory",
             r"regulat\w*", r"legislation", r"bill", r"policy", r"parliament", r"lok sabha", r"rajya sabha",
             r"सरकार", r"मंत्री", r"मंत्रालय", r"कानून", r"संसद", r"एडवाइजरी"])

# Women public figures who appear in Indian deepfake coverage. Only used to group articles about the same
# case into one incident. Add names as they appear in the headlines.
PUBLIC_FIGURES = {
    "rashmika": [r"rashmika", r"रश्मिका"], "katrina": [r"katrina", r"कटरीना", r"कैटरीना"],
    "kajol": [r"kajol", r"काजोल"], "alia": [r"alia bhatt", r"आलिया"],
    "sara_tendulkar": [r"sara tendulkar", r"सारा तेंदुलकर", r"tendulkar's daughter", r"तेंदुलकर की बेटी"], "priyanka": [r"priyanka chopra", r"प्रियंका चोपड़ा"],
    "deepika": [r"deepika", r"दीपिका"], "nora": [r"nora fatehi", r"नोरा"], "janhvi": [r"janhvi", r"जान्हवी"],
    "shraddha": [r"shraddha kapoor", r"श्रद्धा कपूर"], "anushka": [r"anushka", r"अनुष्का"],
    "tamannaah": [r"tamannaah?", r"तमन्ना भाटिया"], "kriti": [r"kriti sanon", r"कृति सेनन"],
    "madhuri": [r"madhuri", r"माधुरी"], "aishwarya": [r"aishwarya", r"ऐश्वर्या"],
    "kiara": [r"kiara", r"कियारा"], "samantha": [r"samantha", r"सामंथा"], "rakul": [r"rakul", r"रकुल"],
    "pooja_hegde": [r"pooja hegde"], "keerthy": [r"keerthy suresh"], "nayanthara": [r"nayanthara"],
    "sai_pallavi": [r"sai pallavi"], "mrunal": [r"mrunal", r"मृणाल"], "sonnalli": [r"sonnalli", r"sonali seygall"],
    "smriti_mandhana": [r"smriti mandhana", r"स्मृति मंधाना"], "sania": [r"sania mirza", r"सानिया"],
    "shilpa": [r"shilpa shetty", r"शिल्पा शेट्टी"], "kareena": [r"kareena", r"करीना"],
    "sonakshi": [r"sonakshi", r"सोनाक्षी"], "jacqueline": [r"jacqueline", r"जैकलीन"],
    "urfi": [r"urfi", r"उर्फी"], "avneet": [r"avneet kaur", r"अवनीत"], "ananya": [r"ananya panday", r"अनन्या"],
    "girija_oak": [r"girija oak"], "anjali_arora": [r"anjali arora", r"अंजलि अरोड़ा"],
    "mamata": [r"mamata banerjee", r"ममता बनर्जी"], "smriti_irani": [r"smriti irani", r"स्मृति ईरानी"],
    "nirmala": [r"nirmala sitharaman", r"निर्मला सीतारमण"], "kangana": [r"kangana", r"कंगना"],
    "mahua": [r"mahua moitra", r"महुआ मोइत्रा"], "taapsee": [r"taapsee", r"तापसी"],
    "neha_singh_rathore": [r"neha singh rathore", r"नेहा सिंह राठौर"],
}
PF_RX = {k: rx(v) for k, v in PUBLIC_FIGURES.items()}
PUBLIC_ROLE = rx([r"actress", r"actor", r"star", r"celeb\w*", r"bollywood", r"tollywood", r"influencer",
                  r"youtuber", r"journalist", r"anchor", r"mla", r"mp", r"minister", r"politician", r"cricketer",
                  r"singer", r"अभिनेत्री", r"एक्ट्रेस", r"विधायक", r"सांसद", r"पत्रकार", r"गायिका", r"इन्फ्लुएंसर"])
LEAD_IN = re.compile(r"^(?:after|post|following)\b[^,:]*[,:]|^.*?के बाद (?:अब )?", re.I)

STATE_RX = {s: rx([re.escape(n) for n in names]) for s, names in STATES.items()}
FOREIGN_RX = rx([re.escape(w.strip()) for w in FOREIGN])
STOP = set("""the a an of to in on for and with by from at as is are was were be has have had after over into his her
their its this that who which man men youth held arrested woman women girl girls photos photo video videos images
case cases police says said said, accused against social media online two three four police, news""".split())


def parse(raw):
    rows = []
    for path in sorted(glob.glob(os.path.join(raw, "*.xml"))):
        head, body = open(path, encoding="utf-8").read().split("\n", 1)
        meta = dict(re.findall(r"(\w+)=(.*?)(?= \w+=| -->)", head))
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            print("  unreadable", path)
            continue
        for it in root.iter("item"):
            src = it.findtext("source") or ""
            title = it.findtext("title") or ""
            if src and title.endswith(" - " + src):
                title = title[: -len(src) - 3]
            try:
                d = parsedate_to_datetime(it.findtext("pubDate")).date()
            except Exception:
                continue
            rows.append({"date": d, "title": title.strip(), "outlet": src, "link": it.findtext("link"),
                         "lang": meta.get("lang"), "query": meta.get("query"),
                         "window_start": meta.get("after"), "window_end": meta.get("before")})
    df = pd.DataFrame(rows)
    # One row per headline+outlet; keep the queries that found it.
    df["key"] = df.title.str.lower().str.replace(r"\W+", " ", regex=True).str.strip() + "|" + df.outlet.str.lower()
    q = df.groupby("key")["query"].apply(lambda s: "; ".join(sorted(set(s))))
    df = df.sort_values("date").drop_duplicates("key").set_index("key")
    df["queries"] = q
    return df.reset_index(drop=True)


def public_figures(t):
    """Public figures named in a headline, minus those only in an 'After X, ...' lead-in."""
    s = LEAD_IN.sub("", t, count=1)
    hits = [k for k, r in PF_RX.items() if r.search(s)] or [k for k, r in PF_RX.items() if r.search(t)]
    return hits


def main_figure(df):
    """With several names in one headline, pick the one with the most coverage that month: 'Mrunal Thakur
    supports Rashmika' belongs to the Rashmika case."""
    names = df.title.map(public_figures)
    month = pd.to_datetime(df.date).dt.to_period("M")
    load = pd.Series([(m, k) for m, ks in zip(month, names) for k in ks]).value_counts()
    return [max(ks, key=lambda k: load.get((m, k), 0)) if ks else "" for m, ks in zip(month, names)]


def classify(df):
    t = df.title
    f = lambda r: t.map(lambda x: bool(r.search(x)))
    df["ai"], df["morph"], df["sexual"], df["media"] = f(AI), f(MORPH), f(SEXUAL), f(MEDIA)
    df["female"], df["minor"], df["police"], df["viral"] = f(FEMALE), f(MINOR), f(POLICE), f(VIRAL)
    df["blackmail"], df["suicide"], df["explainer"], df["policy"] = f(BLACKMAIL), f(SUICIDE), f(EXPLAINER), f(POLICY)
    df["public_figure"] = main_figure(df)
    df["female"] |= df.public_figure.ne("")
    df["public_role"] = f(PUBLIC_ROLE) | df.public_figure.ne("")
    states = t.map(lambda x: sorted(s for s, r in STATE_RX.items() if r.search(x)))
    df["state"] = states.map(lambda s: s[0] if len(s) == 1 else "")
    df["state_candidates"] = states.map("; ".join)
    # Outlet country, learnt from the corpus: an outlet whose headlines often name an Indian place, or that
    # publishes in Hindi, is treated as Indian.
    out = df.outlet.str.lower()
    has_state = states.map(len).gt(0)
    share = has_state.groupby(out).mean()
    n = out.value_counts()
    hindi = df.lang.eq("hi").groupby(out).any()
    known_foreign = {o for o in share.index if any(o.startswith(x) for x in FOREIGN_OUTLETS)}
    indian = {o for o in share.index if o not in known_foreign and (hindi[o] or (n[o] >= 3 and share[o] >= 0.2))}
    df["indian_outlet"] = out.isin(indian)
    df["foreign"] = (f(FOREIGN_RX) | out.isin(known_foreign)) & ~has_state
    # India link: a place, a known Indian public figure, Hindi, or an Indian outlet.
    df["india"] = ~df.foreign & (has_state | df.public_figure.ne("") | df.lang.eq("hi") | df.indian_outlet)

    df["image_type"] = "real_or_unspecified"
    df.loc[df.morph, "image_type"] = "morphed"
    df.loc[df.ai, "image_type"] = "ai_deepfake"
    synthetic = df.ai | df.morph
    abuse_image = synthetic | (df.sexual & df.media)
    # In scope: an India story about a (sexualised or synthetic) image of a woman or girl being made or spread,
    # reported as an event (police action, or it went viral / someone was targeted), not an explainer/policy piece.
    event = df.police | df.viral | df.public_figure.ne("")
    df["in_scope"] = (abuse_image & df.female & (df.sexual | synthetic) & event & df.india
                      & ~(df.explainer & ~df.police))
    df["crime_report"] = df.in_scope & df.police & ~(df.policy & ~df.public_figure.eq("") & ~df.state.ne(""))
    return df


def tokens(t):
    w = re.findall(rf"[a-z{DEV}][a-z0-9{DEV}]{{3,}}", t.lower())
    return {x for x in w if x not in STOP}


def cluster(df, days=10, celeb_days=45, jac=0.3):
    """Group in-scope articles into incidents (union-find).
    Same public figure within celeb_days -> same incident. Otherwise: within `days`, compatible state, and
    headline word overlap (Jaccard) >= jac."""
    d = df[df.in_scope].sort_values("date").reset_index()
    parent = list(range(len(d)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    toks = [tokens(x) for x in d.title]
    dates = pd.to_datetime(d.date).values.astype("datetime64[D]").astype(int)
    last_pf = {}
    for i in range(len(d)):
        pf = d.public_figure[i]
        if pf:
            j = last_pf.get(pf)
            if j is not None and dates[i] - dates[j] <= celeb_days:
                parent[find(i)] = find(j)
            last_pf[pf] = i
            continue
        for j in range(i - 1, -1, -1):
            if dates[i] - dates[j] > days:
                break
            if d.public_figure[j]:
                continue
            si, sj = d.state[i], d.state[j]
            if si and sj and si != sj:
                continue
            u = len(toks[i] | toks[j]) or 1
            if len(toks[i] & toks[j]) / u >= (jac if (si and sj) else jac + 0.15):
                parent[find(i)] = find(j)
    d["incident"] = [find(i) for i in range(len(d))]
    first = d.groupby("incident").date.transform("min")
    order = {k: n for n, k in enumerate(d.assign(f=first).sort_values(["f", "incident"]).incident.unique())}
    d["incident_id"] = d.incident.map(lambda k: f"N{order[k] + 1:05d}")
    return d.set_index("index")["incident_id"]


def summarise(a):
    a = a[a.incident_id.notna()].sort_values("date")
    rank = {"ai_deepfake": 2, "morphed": 1, "real_or_unspecified": 0}
    rows = []
    for k, g in a.groupby("incident_id"):
        st = g.state[g.state.ne("")]
        rep = g[g.police].iloc[0] if g.police.any() else g.iloc[0]
        rows.append({
            "incident_id": k, "first_date": g.date.min(), "year": g.date.min().year,
            "last_date": g.date.max(), "state": st.mode().iloc[0] if len(st) else "",
            "image_type": max(g.image_type, key=rank.get),
            "public_figure": g.public_figure[g.public_figure.ne("")].mode().iloc[0] if g.public_figure.ne("").any() else "",
            "public_figure_or_role": bool(g.public_role.any()),
            "minor_mentioned": bool(g.minor.any()), "sexual_term": bool(g.sexual.any()),
            "police_action": bool(g.police.any()), "blackmail": bool(g.blackmail.any()), "suicide": bool(g.suicide.any()),
            "n_articles": len(g), "n_outlets": g.outlet.nunique(), "langs": "; ".join(sorted(g.lang.unique())),
            "headline": rep.title, "outlet": rep.outlet, "link": rep.link,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default="data/external/news")
    ap.add_argument("out", nargs="?", default="data/clean")
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--end", default="2024-12-31")
    args = ap.parse_args()

    a = parse(os.path.join(args.src, "raw"))
    a = a[(a.date >= pd.Timestamp(args.start).date()) & (a.date <= pd.Timestamp(args.end).date())].copy()
    a = classify(a)
    a["incident_id"] = cluster(a)
    inc = summarise(a)
    a = a.sort_values(["date", "title"])

    cols = ["date", "title", "outlet", "lang", "state", "state_candidates", "image_type", "in_scope", "crime_report",
            "incident_id", "public_figure", "public_role", "female", "minor", "sexual", "media", "ai", "morph",
            "police", "viral", "blackmail", "suicide", "explainer", "policy", "foreign", "indian_outlet", "india",
            "queries", "link"]
    a[cols].to_csv(os.path.join(args.out, "news_articles.csv"), index=False)
    inc.to_csv(os.path.join(args.out, "news_incidents.csv"), index=False)

    sy = (inc.assign(state=inc.state.replace("", "Unknown"))
          .pivot_table(index=["state", "year"], columns="image_type", values="incident_id", aggfunc="count", fill_value=0))
    sy["all_incidents"] = sy.sum(axis=1)
    sy["with_police_action"] = inc.assign(state=inc.state.replace("", "Unknown")).groupby(["state", "year"]).police_action.sum()
    sy["private_individual"] = inc[~inc.public_figure_or_role].assign(state=lambda x: x.state.replace("", "Unknown")).groupby(["state", "year"]).size()
    sy = sy.fillna(0).astype(int).reset_index()
    sy.to_csv(os.path.join(args.out, "news_incidents_state_year.csv"), index=False)

    ins, outs = a[a.in_scope], a[~a.in_scope & (a.ai | a.morph | a.sexual)]
    val = pd.concat([ins.sample(min(150, len(ins)), random_state=1), outs.sample(min(50, len(outs)), random_state=1)])
    val = val[["date", "title", "outlet", "state", "image_type", "in_scope", "crime_report", "link"]]
    for c in ["label_in_scope", "label_state", "label_image_type", "notes"]:
        val[c] = ""
    val.sample(frac=1, random_state=2).to_csv(os.path.join(args.out, "news_validation_sample.csv"), index=False)

    print(f"{len(a)} unique headlines, {int(a.in_scope.sum())} in scope, {len(inc)} incidents")
    print(inc.groupby(["year", "image_type"]).size().unstack(fill_value=0).assign(total=lambda x: x.sum(axis=1)))
    print("state known:", f"{inc.state.ne('').mean():.0%}", " police action:", f"{inc.police_action.mean():.0%}")


if __name__ == "__main__":
    main()
