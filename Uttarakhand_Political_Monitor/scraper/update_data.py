# -*- coding: utf-8 -*-
"""
Uttarakhand Political Monitor - auto updater (bilkul free).

Kya karta hai:
  1. Google News RSS (aur config.DIRECT_FEEDS) se UK / UP / HP / National ki rajnitik khabrein laata hai.
  2. Purani khabron ke saath milakar duplicate hatata hai, category / severity / sentiment lagata hai.
  3. Top-10 trending issue banata hai (jo khabar sabse zyada portals par hai).
  4. data.json + initial_data.js likhta hai (dashboard yahi padhta hai) aur
     archive/YYYY/MM/YYYY-MM-DD.json me roz ka record hamesha ke liye rakhta hai.
  5. Social War Room (X radar) aur Battleground matrix ko manual/ folder ya purane data se
     waise hi rakhta hai; battleground me "keywords" diye ho to uske "latest_3_updates" khud bharta hai.

Chalane ka tarika (local):  python scraper/update_data.py
GitHub Actions har 15 minute me ise khud chalata hai.
"""
import os
import re
import sys
import json
import time
import hashlib
import difflib
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import feedparser
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Uttarakhand_Political_Monitor/
DATA_JSON = os.path.join(BASE, "data.json")
INITIAL_JS = os.path.join(BASE, "initial_data.js")
ARCHIVE_DIR = os.path.join(BASE, "archive")
MANUAL_DIR = os.path.join(BASE, "manual")
UA = "Mozilla/5.0 (compatible; PoliticalMonitorBot/1.0; +https://github.com)"

HINDI_MONTHS = ["\u091c\u0928", "\u092b\u0930", "\u092e\u093e\u0930\u094d\u091a", "\u0905\u092a\u094d\u0930\u0948", "\u092e\u0908", "\u091c\u0942\u0928", "\u091c\u0941\u0932\u093e", "\u0905\u0917", "\u0938\u093f\u0924\u0902", "\u0905\u0915\u094d\u091f\u0942", "\u0928\u0935\u0902", "\u0926\u093f\u0938\u0902"]
STATE_LABELS = {
    "Uttarakhand": "\U0001f3d4\ufe0f \u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0902\u0921",
    "Uttar Pradesh": "\U0001f3db\ufe0f \u0909\u0924\u094d\u0924\u0930 \u092a\u094d\u0930\u0926\u0947\u0936",
    "Himachal Pradesh": "\U0001f332 \u0939\u093f\u092e\u093e\u091a\u0932 \u092a\u094d\u0930\u0926\u0947\u0936",
    "National": "\U0001f1ee\U0001f1f3 \u0930\u093e\u0937\u094d\u091f\u094d\u0930\u0940\u092f",
}


# ------------------------------------------------------------------ helpers
def now_ist():
    return datetime.now(IST)


def clean_text(s, limit=None):
    """Dashboard onclick me text quotes ke beech jaata hai, isliye quotes/HTML ko safe banao."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(s))          # HTML tags hatao
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", "\u201d")
           .replace("&#39;", "\u2019").replace("&lt;", "").replace("&gt;", ""))
    s = s.replace('"', "\u201d").replace("'", "\u2019").replace("`", "\u2019").replace("\\", "/")
    s = s.replace("<", "").replace(">", "")
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        s = s[: limit - 1].rstrip() + "\u2026"
    return s


def norm_title(t):
    t = t.lower()
    t = re.sub(r"[^\w\u0900-\u097f ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def contains_any(text, words):
    padded = " " + text.lower() + " "
    return any(w.lower() in padded for w in words)


def match_publisher(name):
    if not name:
        return ""
    low = name.lower().strip()
    for k, v in C.PUBLISHER_ALIASES.items():
        if k in low:
            return v
    return name.strip()


def detect_state(text, fallback):
    hits = {s: sum(1 for w in kws if w.lower() in (" " + text.lower() + " ")) for s, kws in C.STATE_KEYWORDS.items()}
    best = max(hits, key=hits.get)
    if fallback in ("National", "AUTO"):
        # National query wali khabar agar kisi state ki nikle to us state me daalo
        return best if hits[best] > 0 else "National"
    # state-wise query se aayi khabar usi state ki, jab tak text saaf taur par kisi aur state ka na ho
    if hits.get(fallback, 0) == 0 and hits[best] > 0:
        return best
    return fallback


def date_tag_for(dt):
    today = now_ist().date()
    d = dt.astimezone(IST).date()
    diff = (today - d).days
    if diff <= 0:
        return "today"
    if diff == 1:
        return "yesterday"
    if diff <= 7:
        return "7d"
    if diff <= 30:
        return "30d"
    return "old"


def date_label_for(dt):
    d = dt.astimezone(IST)
    return f"{d.day:02d} {HINDI_MONTHS[d.month - 1]}, {d:%H:%M}"


def classify(text):
    category = C.DEFAULT_CATEGORY
    for cat, words in C.CATEGORY_RULES:
        if contains_any(text, words):
            category = cat
            break
    severity = "High" if contains_any(text, C.HIGH_ALERT_WORDS) else "Medium"
    if contains_any(text, C.NEGATIVE_WORDS):
        sentiment = "Negative"
    elif contains_any(text, C.POSITIVE_WORDS):
        sentiment = "Positive"
    else:
        sentiment = "Neutral"
    return category, severity, sentiment


IMPACT_TEMPLATES = {
    "\u091a\u0941\u0928\u093e\u0935": "\u091a\u0941\u0928\u093e\u0935\u0940 \u0938\u092e\u0940\u0915\u0930\u0923 \u0914\u0930 \u0926\u0932\u094b\u0902 \u0915\u0940 \u0930\u0923\u0928\u0940\u0924\u093f \u092a\u0930 \u0938\u0940\u0927\u093e \u0905\u0938\u0930; \u0906\u0928\u0947 \u0935\u093e\u0932\u0947 \u0926\u093f\u0928\u094b\u0902 \u092e\u0947\u0902 \u092c\u092f\u093e\u0928\u092c\u093e\u091c\u093c\u0940 \u0924\u0947\u091c\u093c \u0939\u094b\u0928\u0947 \u0915\u0940 \u0938\u0902\u092d\u093e\u0935\u0928\u093e\u0964",
    "\u0935\u093f\u0930\u094b\u0927/\u0906\u0902\u0926\u094b\u0932\u0928": "\u0938\u0930\u0915\u093e\u0930 \u092a\u0930 \u0926\u092c\u093e\u0935 \u092c\u0922\u093c\u093e\u0928\u0947 \u0935\u093e\u0932\u093e \u092e\u0941\u0926\u094d\u0926\u093e; \u0935\u093f\u092a\u0915\u094d\u0937 \u0907\u0938\u0947 \u091c\u0928-\u0905\u0938\u0902\u0924\u094b\u0937 \u0915\u0947 \u0930\u0942\u092a \u092e\u0947\u0902 \u0909\u0920\u093e \u0938\u0915\u0924\u093e \u0939\u0948\u0964",
    "\u092d\u094d\u0930\u0937\u094d\u091f\u093e\u091a\u093e\u0930/\u0918\u094b\u091f\u093e\u0932\u093e": "\u0938\u0924\u094d\u0924\u093e \u092a\u0915\u094d\u0937 \u0915\u0940 \u091b\u0935\u093f \u092a\u0930 \u0905\u0938\u0930; \u0935\u093f\u092a\u0915\u094d\u0937 \u0915\u0947 \u0932\u093f\u090f \u0939\u092e\u0932\u0947 \u0915\u093e \u092c\u0921\u093c\u093e \u092e\u0941\u0926\u094d\u0926\u093e \u092c\u0928 \u0938\u0915\u0924\u093e \u0939\u0948\u0964",
    "\u0915\u093e\u0928\u0942\u0928-\u0935\u094d\u092f\u0935\u0938\u094d\u0925\u093e": "\u0915\u093e\u0928\u0942\u0928-\u0935\u094d\u092f\u0935\u0938\u094d\u0925\u093e \u092a\u0930 \u0938\u0935\u093e\u0932; \u0938\u0930\u0915\u093e\u0930 \u0915\u0940 \u091c\u0935\u093e\u092c\u0926\u0947\u0939\u0940 \u0915\u094b \u0932\u0947\u0915\u0930 \u0930\u093e\u091c\u0928\u0940\u0924\u093f\u0915 \u092c\u0939\u0938 \u0938\u0902\u092d\u0935\u0964",
    "\u0906\u092a\u0926\u093e/\u092a\u0930\u094d\u092f\u093e\u0935\u0930\u0923": "\u0930\u093e\u0939\u0924-\u092c\u091a\u093e\u0935 \u0914\u0930 \u092a\u094d\u0930\u0936\u093e\u0938\u0928\u093f\u0915 \u0924\u0948\u092f\u093e\u0930\u0940 \u092a\u0930 \u0938\u0930\u0915\u093e\u0930 \u0915\u0940 \u092a\u0930\u0940\u0915\u094d\u0937\u093e; \u0935\u093f\u092a\u0915\u094d\u0937 \u0938\u0935\u093e\u0932 \u0909\u0920\u093e \u0938\u0915\u0924\u093e \u0939\u0948\u0964",
    "\u0935\u093f\u0915\u093e\u0938/\u092f\u094b\u091c\u0928\u093e": "\u0938\u0930\u0915\u093e\u0930 \u0915\u0947 \u0935\u093f\u0915\u093e\u0938 \u0928\u0948\u0930\u0947\u091f\u093f\u0935 \u0915\u094b \u092e\u091c\u093c\u092c\u0942\u0924\u0940; \u0938\u0924\u094d\u0924\u093e \u092a\u0915\u094d\u0937 \u0907\u0938\u0947 \u0909\u092a\u0932\u092c\u094d\u0927\u093f \u0915\u0947 \u0930\u0942\u092a \u092e\u0947\u0902 \u092a\u094d\u0930\u091a\u093e\u0930\u093f\u0924 \u0915\u0930\u0947\u0917\u093e\u0964",
    "\u0938\u0902\u0917\u0920\u0928/\u0926\u0932": "\u0926\u0932 \u0915\u0947 \u0905\u0902\u0926\u0930\u0942\u0928\u0940 \u0938\u092e\u0940\u0915\u0930\u0923 \u0914\u0930 \u0938\u0902\u0917\u0920\u0928\u093e\u0924\u094d\u092e\u0915 \u092e\u091c\u093c\u092c\u0942\u0924\u0940 \u092a\u0930 \u0905\u0938\u0930\u0964",
    "\u0928\u094d\u092f\u093e\u092f\u093e\u0932\u092f": "\u0905\u0926\u093e\u0932\u0924\u0940 \u0930\u0941\u0916 \u0938\u0947 \u0938\u0930\u0915\u093e\u0930/\u0926\u0932\u094b\u0902 \u0915\u0940 \u0938\u094d\u0925\u093f\u0924\u093f \u092a\u094d\u0930\u092d\u093e\u0935\u093f\u0924; \u0906\u0917\u0947 \u0915\u0940 \u0938\u0941\u0928\u0935\u093e\u0908 \u092a\u0930 \u0928\u091c\u093c\u0930\u0964",
}


def rule_based_analysis(item, summary):
    item["what_issue"] = clean_text(summary or item["headline"], 400)
    item["why_context"] = clean_text(
        f"{item['source']} \u0915\u0940 \u0930\u093f\u092a\u094b\u0930\u094d\u091f \u2022 \u0936\u094d\u0930\u0947\u0923\u0940: {item['category']} \u2022 {STATE_LABELS.get(item['state'], '')}", 200)
    item["political_impact"] = IMPACT_TEMPLATES.get(
        item["category"], "\u0930\u093e\u091c\u094d\u092f \u0915\u0947 \u0930\u093e\u091c\u0928\u0940\u0924\u093f\u0915 \u0935\u093f\u092e\u0930\u094d\u0936 \u092e\u0947\u0902 \u091a\u0930\u094d\u091a\u093e \u0915\u093e \u0935\u093f\u0937\u092f; \u0926\u0932\u094b\u0902 \u0915\u0940 \u092a\u094d\u0930\u0924\u093f\u0915\u094d\u0930\u093f\u092f\u093e \u092a\u0930 \u0928\u091c\u093c\u0930 \u0930\u0916\u0947\u0902\u0964")
    item["ai"] = False


# ------------------------------------------------------------------ fetching
def gnews_url(query):
    q = quote_plus(f"{query} when:2d")
    return f"https://news.google.com/rss/search?q={q}&hl=hi&gl=IN&ceid=IN:hi"


def fetch_feed(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:  # ek feed fail ho to baaki chalte rahen
        print(f"  ! feed fail: {url[:90]} -> {e}")
        return None


def entry_datetime(e):
    for key in ("published_parsed", "updated_parsed"):
        t = e.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def parse_entries(feed, state_hint, portal_hint=None):
    out = []
    if not feed:
        return out
    for e in feed.entries[: C.MAX_ITEMS_PER_QUERY]:
        title = e.get("title", "")
        publisher = ""
        src = e.get("source")
        if src and getattr(src, "title", None):
            publisher = src.title
        elif isinstance(src, dict):
            publisher = src.get("title", "")
        # Google News title = "Headline - Publisher"
        if " - " in title:
            head, tail = title.rsplit(" - ", 1)
            if not publisher or tail.strip().lower() in publisher.lower() or publisher.lower() in tail.lower():
                publisher = publisher or tail
                title = head
        publisher = match_publisher(publisher or portal_hint) or "\u0938\u092e\u093e\u091a\u093e\u0930 \u092a\u094b\u0930\u094d\u091f\u0932"
        summary = e.get("summary", "")
        # Google News summary me sirf title+link hota hai, use hatao
        if norm_title(clean_text(summary)).startswith(norm_title(title)[:30]):
            summary = ""
        out.append({
            "title": title,
            "summary": summary,
            "link": e.get("link", ""),
            "publisher": publisher,
            "dt": entry_datetime(e),
            "state_hint": state_hint,
        })
    return out


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "hi-IN,hi;q=0.9,en;q=0.8",
}


def parse_iso(s):
    try:
        dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=IST)
    except Exception:
        return None


def walk_dicts(obj):
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            yield o
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)


def parse_etv_page(html, base="https://www.etvbharat.com/"):
    """ETV Bharat (Next.js): __NEXT_DATA__ me khabron ki list hoti hai (kabhi base64 me)."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw.startswith("{"):
        import base64
        raw = base64.b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8", "ignore")
    data = json.loads(raw)
    out, seen = [], set()
    for d in walk_dicts(data):
        title = d.get("display_title") or d.get("title")
        url = d.get("web_url")
        when = parse_iso(d.get("publish_date_string") or d.get("updated_at") or "")
        if not (isinstance(title, str) and isinstance(url, str) and when) or url in seen:
            continue
        seen.add(url)
        link = url if url.startswith("http") else base + url.lstrip("/")
        out.append({"title": title, "summary": d.get("short_description") or "", "link": link, "dt": when})
    return out


def parse_bhaskar_page(html, base="https://www.bhaskar.com"):
    """Dainik Bhaskar: window.INITIAL_STATE me feed hota hai (headline = header.slug)."""
    m = re.search(r"window\.INITIAL_STATE\s*=\s*(\{.*?\})\s*;?\s*</script>", html, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    out, seen = [], set()
    for d in walk_dicts(data):
        sid, header = d.get("storyId"), d.get("header")
        if not sid or not isinstance(header, dict) or sid in seen:
            continue
        when = parse_iso(d.get("publishTime") or d.get("modifiedTime") or "")
        title = header.get("slug") or header.get("title")
        short = d.get("shortUrl") or ""
        if not (title and when and short):
            continue
        seen.add(sid)
        link = base + short if short.endswith(".html") else f"{base}{short}-{sid}.html"
        out.append({"title": title, "summary": header.get("title") if header.get("slug") else "",
                    "link": link, "dt": when})
    return out


PAGE_PARSERS = {"etv": parse_etv_page, "bhaskar": parse_bhaskar_page}


def collect_pages():
    raw = []
    for portal, state, url, kind in getattr(C, "PAGE_SOURCES", []):
        try:
            r = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
            r.raise_for_status()
            rows = PAGE_PARSERS[kind](r.text)
        except Exception as e:  # ek site fail ho to baaki chalte rahen
            print(f"  ! page fail: {portal} {state} -> {e}")
            continue
        for row in rows[: C.MAX_ITEMS_PER_QUERY * 2]:
            row.update({"publisher": portal, "state_hint": state})
            raw.append(row)
        print(f"[page] {state:16s} {portal:16s} +{len(rows)}")
        time.sleep(1)
    return raw


def collect_raw():
    jobs = []
    for state, queries in C.STATE_QUERIES.items():
        for q in queries:
            jobs.append((gnews_url(q), state, None))
    for portal, site in C.PORTAL_SITES.items():
        for state, words in C.PORTAL_STATE_WORDS.items():
            jobs.append((gnews_url(f"site:{site} ({words})"), state, portal))
    for portal, state, url in C.DIRECT_FEEDS:
        jobs.append((url, state, portal))

    raw = []
    for i, (url, state, portal) in enumerate(jobs, 1):
        feed = fetch_feed(url)
        got = parse_entries(feed, state, portal)
        raw.extend(got)
        print(f"[{i}/{len(jobs)}] {state:16s} {portal or '':16s} +{len(got)}")
        time.sleep(0.6)  # Google ko spam na lage
    raw.extend(collect_pages())
    return raw


# ------------------------------------------------------------------ build items
def make_id(link, title):
    return int(hashlib.md5((norm_title(title) or link).encode("utf-8")).hexdigest()[:12], 16) % 10**12


def build_item(r):
    headline = clean_text(r["title"], 220)
    text = f"{headline} {clean_text(r['summary'])}"
    if not contains_any(text, C.POLITICAL_KEYWORDS):
        return None
    state = detect_state(text, r["state_hint"])
    category, severity, sentiment = classify(text)
    dt = r["dt"]
    item = {
        "id": make_id(r["link"], headline),
        "headline": headline,
        "state": state,
        "category": category,
        "severity": severity,
        "sentiment": sentiment,
        "source": clean_text(r["publisher"], 60),
        "link": r["link"],
        "pub_date": dt.astimezone(IST).strftime("%d-%m-%Y %H:%M IST"),
        "pub_ts": dt.astimezone(timezone.utc).isoformat(),
        "detected_at": now_ist().strftime("%d-%m-%Y %H:%M IST"),
        "date_tag": date_tag_for(dt),
        "date_label": date_label_for(dt),
        "other_sources": [],
    }
    rule_based_analysis(item, r["summary"])
    return item


def similar(a, b):
    return difflib.SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def merge(existing, new_items):
    """Purani + nayi khabrein. Same/milti-julti headline = ek hi item, dusre portal 'other_sources' me."""
    by_id = {it["id"]: it for it in existing}
    recent = sorted(existing, key=lambda x: x.get("pub_ts", ""), reverse=True)[:400]
    added = []
    for it in new_items:
        if it["id"] in by_id:
            continue
        dup = None
        for old in recent + added:
            if similar(old["headline"], it["headline"]) > 0.82:
                dup = old
                break
        if dup:
            if it["source"] != dup["source"] and it["source"] not in dup.get("other_sources", []):
                dup.setdefault("other_sources", []).append(it["source"])
            continue
        by_id[it["id"]] = it
        added.append(it)
    return list(by_id.values()), added


# ------------------------------------------------------------------ optional AI (Gemini free tier)
def ai_enrich(items):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or not items:
        return 0
    model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    todo = items[: C.AI_MAX_NEW_ITEMS_PER_RUN]
    done = 0
    for start in range(0, len(todo), C.AI_BATCH_SIZE):
        batch = todo[start:start + C.AI_BATCH_SIZE]
        listing = "\n".join(f'{i}. [{b["state"]}] {b["headline"]} ({b["source"]})' for i, b in enumerate(batch))
        prompt = (
            "\u0924\u0941\u092e \u090f\u0915 \u092d\u093e\u0930\u0924\u0940\u092f \u0930\u093e\u091c\u0928\u0940\u0924\u093f\u0915 \u092e\u0940\u0921\u093f\u092f\u093e \u0935\u093f\u0936\u094d\u0932\u0947\u0937\u0915 \u0939\u094b\u0964 \u0928\u0940\u091a\u0947 \u0926\u0940 \u0917\u0908 \u0939\u0930 \u0916\u092c\u0930 \u0915\u0947 \u0932\u093f\u090f \u0924\u091f\u0938\u094d\u0925, \u0924\u0925\u094d\u092f\u093e\u0924\u094d\u092e\u0915 \u0939\u093f\u0902\u0926\u0940 \u092e\u0947\u0902 JSON \u0926\u094b\u0964 "
            "\u0915\u0947\u0935\u0932 \u0939\u0947\u0921\u0932\u093e\u0907\u0928 \u092e\u0947\u0902 \u092e\u094c\u091c\u0942\u0926 \u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u0915\u093e \u092a\u094d\u0930\u092f\u094b\u0917 \u0915\u0930\u094b, \u0915\u094b\u0908 \u0928\u093e\u092e/\u092a\u0926/\u0906\u0902\u0915\u0921\u093c\u093e \u0905\u092a\u0928\u0940 \u0913\u0930 \u0938\u0947 \u092e\u0924 \u091c\u094b\u0921\u093c\u094b\u0964\n"
            "\u0939\u0930 \u0916\u092c\u0930 \u0915\u0947 \u0932\u093f\u090f keys: idx (\u0938\u0902\u0916\u094d\u092f\u093e), what_issue (1-2 \u0935\u093e\u0915\u094d\u092f: \u0915\u094d\u092f\u093e \u0939\u0941\u0906), why_context (1 \u0935\u093e\u0915\u094d\u092f: \u0915\u094d\u092f\u094b\u0902 \u092e\u0939\u0924\u094d\u0935\u092a\u0942\u0930\u094d\u0923), "
            "political_impact (1 \u0935\u093e\u0915\u094d\u092f: \u0930\u093e\u091c\u0928\u0940\u0924\u093f\u0915 \u0905\u0938\u0930), category (\u0907\u0928\u092e\u0947\u0902 \u0938\u0947 \u090f\u0915: \u091a\u0941\u0928\u093e\u0935, \u0935\u093f\u0930\u094b\u0927/\u0906\u0902\u0926\u094b\u0932\u0928, \u092d\u094d\u0930\u0937\u094d\u091f\u093e\u091a\u093e\u0930/\u0918\u094b\u091f\u093e\u0932\u093e, "
            "\u0915\u093e\u0928\u0942\u0928-\u0935\u094d\u092f\u0935\u0938\u094d\u0925\u093e, \u0906\u092a\u0926\u093e/\u092a\u0930\u094d\u092f\u093e\u0935\u0930\u0923, \u0935\u093f\u0915\u093e\u0938/\u092f\u094b\u091c\u0928\u093e, \u0938\u0902\u0917\u0920\u0928/\u0926\u0932, \u0928\u094d\u092f\u093e\u092f\u093e\u0932\u092f, \u0930\u093e\u091c\u0928\u0940\u0924\u093f\u0915 \u0905\u092a\u0921\u0947\u091f), severity (High \u092f\u093e Medium), "
            "sentiment (Positive, Negative \u092f\u093e Neutral)\u0964\n"
            "\u0915\u0947\u0935\u0932 JSON array \u0932\u094c\u091f\u093e\u0913\u0964\n\n" + listing
        )
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
        try:
            r = requests.post(url, params={"key": key}, json=body, timeout=60)
            r.raise_for_status()
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            arr = json.loads(txt)
        except Exception as e:
            print(f"  ! AI skip (free limit / error): {e}")
            break
        for row in arr if isinstance(arr, list) else []:
            try:
                b = batch[int(row["idx"])]
            except Exception:
                continue
            for k in ("what_issue", "why_context", "political_impact"):
                if row.get(k):
                    b[k] = clean_text(row[k], 400)
            if row.get("category"):
                b["category"] = clean_text(row["category"], 40)
            if row.get("severity") in ("High", "Medium"):
                b["severity"] = row["severity"]
            if row.get("sentiment") in ("Positive", "Negative", "Neutral"):
                b["sentiment"] = row["sentiment"]
            b["ai"] = True
            done += 1
        time.sleep(5)  # free tier per-minute limit ka dhyan
    return done


# ------------------------------------------------------------------ top 10 trending
def build_top10(items):
    pool = [i for i in items if i["date_tag"] in ("today", "yesterday")]
    pool.sort(key=lambda x: x.get("pub_ts", ""), reverse=True)
    clusters = []
    for it in pool:
        for c in clusters:
            if similar(c["lead"]["headline"], it["headline"]) > 0.55:
                c["members"].append(it)
                break
        else:
            clusters.append({"lead": it, "members": [it]})

    def score(c):
        sources = set()
        for m in c["members"]:
            sources.add(m["source"])
            sources.update(m.get("other_sources", []))
        sev = sum(1 for m in c["members"] if m["severity"] == "High")
        fresh = 1 if c["lead"]["date_tag"] == "today" else 0
        return (len(sources) * 3 + len(c["members"]) * 2 + sev + fresh * 2, c["lead"].get("pub_ts", "")), sources

    ranked = []
    for c in clusters:
        sc, sources = score(c)
        ranked.append((sc, c, sources))
    ranked.sort(key=lambda x: x[0], reverse=True)

    top = []
    for rank, (_, c, sources) in enumerate(ranked[:10], 1):
        lead = c["lead"]
        top.append({
            "rank": rank,
            "issue": lead["headline"],
            "what_issue": lead["what_issue"],
            "why_context": lead["why_context"],
            "political_impact": lead["political_impact"],
            "source": lead["source"],
            "link": lead["link"],
            "state": lead["state"],
            "state_label": STATE_LABELS.get(lead["state"], "\U0001f1ee\U0001f1f3 \u0930\u093e\u0937\u094d\u091f\u094d\u0930\u0940\u092f"),
            "date_tag": lead["date_tag"],
            "today_context": clean_text(f"{lead['category']} \u2022 {lead['date_label']} \u2022 {', '.join(sorted(sources))[:90]}", 160),
            "buzz": f"\U0001f525 {len(sources)} \u092a\u094b\u0930\u094d\u091f\u0932 \u2022 {len(c['members'])} \u0930\u093f\u092a\u094b\u0930\u094d\u091f",
        })
    return top


# ------------------------------------------------------------------ social radar / battleground
def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_initial_js():
    try:
        with open(INITIAL_JS, encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r"=\s*(\{.*\})\s*;?\s*$", txt, re.S)
        return json.loads(m.group(1)) if m else None
    except Exception:
        return None


def refresh_post_tags(radar):
    """Agar X post me posted_at (YYYY-MM-DD) diya ho to uska date_tag roz apne aap update ho."""
    for party in ("bjp", "inc"):
        for p in (radar.get(party, {}) or {}).get("posts", []) or []:
            if p.get("posted_at"):
                try:
                    dt = datetime.fromisoformat(p["posted_at"]).replace(tzinfo=IST)
                    p["date_tag"] = date_tag_for(dt)
                    p.setdefault("date_str", date_label_for(dt))
                except Exception:
                    pass
    return radar


def refresh_battleground(matrix, items):
    """Battleground item me "keywords": [...] ho to latest 3 updates khabron se khud bharo."""
    ordered = sorted(items, key=lambda x: x.get("pub_ts", ""), reverse=True)
    for bg in matrix:
        kws = bg.get("keywords")
        if not kws:
            continue
        hits = [i for i in ordered
                if (bg.get("state") in (None, "", "National") or i["state"] == bg.get("state"))
                and contains_any(i["headline"] + " " + i.get("what_issue", ""), kws)][:3]
        if hits:
            bg["latest_3_updates"] = [{
                "date": h["date_label"],
                "point": h["headline"],
                "detail": h["what_issue"],
                "source": h["source"],
            } for h in hits]
    return matrix


# ------------------------------------------------------------------ archive
def write_archive(items):
    """
    Roz ka permanent record: archive/YYYY/MM/YYYY-MM-DD.json
    Sirf poore ho chuke dinon (aaj se pehle) ke liye likha jata hai. Kal aur parson ki file me
    der se aayi khabrein jod di jaati hain; usse purane din ki file sirf tab banti hai jab na ho.
    data.json me 30 din ka data hota hai, isliye koi din chhoot jaye to agle run me bhar jata hai.
    """
    today = now_ist().date()
    by_day = {}
    for it in items:
        d = datetime.fromisoformat(it["pub_ts"]).astimezone(IST).date()
        if d < today:
            by_day.setdefault(d, []).append(it)
    changed = 0
    for d, rows in sorted(by_day.items()):
        day = d.strftime("%Y-%m-%d")
        folder = os.path.join(ARCHIVE_DIR, day[:4], day[5:7])
        path = os.path.join(folder, f"{day}.json")
        exists = os.path.exists(path)
        if exists and (today - d).days > 2:
            continue
        old = load_json(path) or []
        seen = {r["id"] for r in old}
        fresh = [r for r in rows if r["id"] not in seen]
        if not fresh:
            continue
        old.extend(fresh)
        old.sort(key=lambda x: x.get("pub_ts", ""))
        os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(old, f, ensure_ascii=False, separators=(",", ":"))
        changed += 1
    return changed


# ------------------------------------------------------------------ Telegram alert (optional)
def send_telegram_alerts(high_items):
    """
    Naye High-alert mudde Telegram par. Token sirf GitHub Secrets se aata hai
    (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) \u2014 code me kabhi mat likhna.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat or not high_items:
        return
    lines = ["\U0001f6a8 <b>\u0930\u093e\u091c\u0928\u0940\u0924\u093f\u0915 \u092e\u0940\u0921\u093f\u092f\u093e \u092e\u0949\u0928\u093f\u091f\u0930 \u2014 \u0928\u090f \u0939\u093e\u0908 \u0905\u0932\u0930\u094d\u091f</b>",
             f"\U0001f4c5 {now_ist().strftime('%d-%m-%Y %H:%M IST')}", ""]
    for n, it in enumerate(high_items[:5], 1):
        head = it["headline"].replace("<", "").replace(">", "").replace("&", "\u0914\u0930")
        lines.append(f"{n}. <b>[{STATE_LABELS.get(it['state'], it['state'])}]</b> {head}")
        lines.append(f"   \u0938\u094d\u0930\u094b\u0924: {it['source']} \u2022 <a href=\"{it['link']}\">\u0916\u092c\u0930 \u092a\u0922\u093c\u0947\u0902</a>")
    if len(high_items) > 5:
        lines.append(f"\n\u2026\u0914\u0930 {len(high_items) - 5} \u0928\u090f \u0939\u093e\u0908 \u0905\u0932\u0930\u094d\u091f \u0921\u0948\u0936\u092c\u094b\u0930\u094d\u0921 \u092a\u0930\u0964")
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": "\n".join(lines), "parse_mode": "HTML",
                                "disable_web_page_preview": True}, timeout=20)
        print(f"Telegram: {r.status_code}")
    except Exception as e:
        print(f"  ! Telegram fail: {e}")


# ------------------------------------------------------------------ main
def main():
    started = now_ist()
    prev = load_json(DATA_JSON) or load_initial_js() or {}
    existing = [i for i in prev.get("issues", []) if i.get("pub_ts")]  # sirf auto-items aage le jao

    raw = collect_raw()
    built = [b for b in (build_item(r) for r in raw) if b]
    print(f"raw={len(raw)} political={len(built)}")

    merged, added = merge(existing, built)
    print(f"new unique={len(added)}")
    ai_done = ai_enrich([a for a in added if a["date_tag"] in ("today", "yesterday")])
    if ai_done:
        print(f"AI analysed={ai_done}")

    # date_tag har run me naye sire se (aaj ki khabar kal 'yesterday' ban jaye)
    for it in merged:
        it["date_tag"] = date_tag_for(datetime.fromisoformat(it["pub_ts"]))
    cutoff = (started - timedelta(days=C.KEEP_DAYS_IN_DASHBOARD)).astimezone(timezone.utc).isoformat()
    merged = [i for i in merged if i["pub_ts"] >= cutoff]
    merged.sort(key=lambda x: x["pub_ts"], reverse=True)
    merged = merged[: C.MAX_ITEMS_IN_DASHBOARD]

    radar_path = os.path.join(MANUAL_DIR, "social_radar.json")
    matrix_path = os.path.join(MANUAL_DIR, "battleground.json")
    radar = load_json(radar_path) or prev.get("party_social_radar") or {"bjp": {}, "inc": {}}
    matrix = load_json(matrix_path) or prev.get("battleground_matrix") or []
    # Pehli baar: purana X radar / battleground manual/ me copy kar do taaki aap use edit kar sako
    os.makedirs(MANUAL_DIR, exist_ok=True)
    for path, obj in ((radar_path, radar), (matrix_path, matrix)):
        if not os.path.exists(path) and obj:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)

    data = {
        "last_updated": started.strftime("%d-%m-%Y %H:%M IST"),
        "generated_at": started.isoformat(),
        "stats": {"total": len(merged), "new_this_run": len(added), "ai_analysed": ai_done},
        "issues": merged,
        "top_10_trending": build_top10(merged),
        "party_social_radar": refresh_post_tags(radar),
        "battleground_matrix": refresh_battleground(matrix, merged),
    }

    if not raw and existing:
        # Network fail hua to purana data mat mitao, sirf time-tags refresh karo
        print("No feeds reachable; keeping previous items.")

    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    # initial_data.js sirf offline (file://) backup hai; din me ek baar likho taaki repo halka rahe
    today_str = started.strftime("%d-%m-%Y")
    old_js = ""
    if os.path.exists(INITIAL_JS):
        with open(INITIAL_JS, encoding="utf-8") as f:
            old_js = f.read(200)
    if today_str not in old_js:
        with open(INITIAL_JS, "w", encoding="utf-8") as f:
            f.write("window.INITIAL_DATA = ")
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            f.write(";\n")
    if existing:  # pehle run me sab khabrein "nayi" hoti hain, tab alert ki baadh na aaye
        send_telegram_alerts([a for a in added if a["severity"] == "High" and a["date_tag"] == "today"])
    days = write_archive(merged)
    print(f"done: {len(merged)} items in dashboard, {len(added)} new, archive days updated={days}, {now_ist() - started} taken")


if __name__ == "__main__":
    main()
