import os, re, json, time, uuid
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
import argparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as dtparse
from sqlalchemy import create_engine, text

API_TIMEOUT = 15
HEADERS = {"User-Agent": "ramblin-recs/ingester (+local)"}
PAST_DAYS_KEEP = 14  # keep events up to 14 days in the past

def _engine():
    url = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/recs")
    return create_engine(url, future=True, pool_pre_ping=True)

def _fetch(url: str):
    r = requests.get(url, headers=HEADERS, timeout=API_TIMEOUT)
    r.raise_for_status()
    return r

def _domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)/", url + "/")
    return m.group(1) if m else "unknown"

# -------- JSON-LD parser for a Localist event page --------
def parse_event_page(url: str) -> dict | None:
    try:
        html = _fetch(url).text
    except Exception:
        return None
    soup = BeautifulSoup(html, "lxml")

    # Prefer JSON-LD
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for obj in items:
            if not isinstance(obj, dict):
                continue
            if obj.get("@type") == "Event" or ("startDate" in obj and "name" in obj):
                name = (obj.get("name") or "").strip()
                desc = (obj.get("description") or "").strip()
                start_raw = obj.get("startDate")
                loc = obj.get("location")
                location = ""
                if isinstance(loc, dict):
                    location = (loc.get("name") or loc.get("address") or "").strip()
                elif isinstance(loc, str):
                    location = loc.strip()
                tags = []
                kw = obj.get("keywords")
                if isinstance(kw, list):
                    tags = [str(k) for k in kw][:8]
                elif isinstance(kw, str):
                    tags = [k.strip() for k in kw.split(",") if k.strip()][:8]

                start = None
                if start_raw:
                    try:
                        dt = dtparse(start_raw)
                        if not dt.tzinfo:
                            dt = dt.replace(tzinfo=timezone.utc)
                        start = dt.astimezone(timezone.utc)
                    except Exception:
                        start = None

                if name and start:
                    return {
                        "title": name,
                        "description": desc,
                        "start_time": start,
                        "location": location,
                        "tags": tags,
                        "url": url,
                    }
    return None

# -------- RSS discovery on https://calendar.gatech.edu/rss-feeds --------
def get_rss_links(rss_page: str) -> list[str]:
    try:
        html = _fetch(rss_page).text
    except Exception:
        return []
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "rss" in href.lower() or href.lower().endswith(".xml"):
            if href.startswith("/"):
                href = urljoin(rss_page, href)
            out.append(href)
    # dedupe preserve order
    seen, uniq = set(), []
    for u in out:
        if u not in seen:
            uniq.append(u); seen.add(u)
    return uniq[:30]

def iter_rss_items(feed_url: str):
    try:
        xml = _fetch(feed_url).text
    except Exception:
        return
    soup = BeautifulSoup(xml, "xml")
    for item in soup.find_all("item"):
        link = (item.findtext("link") or "").strip()
        if link:
            yield {"link": link}

# -------- Upsert helpers --------
def upsert_event(conn, ev: dict) -> int:
    if not ev.get("start_time"):
        return 0
    # keep last N days, drop older
    if ev["start_time"] < datetime.now(timezone.utc) - timedelta(days=PAST_DAYS_KEEP):
        return 0

    # ensure domain tag
    tags = ev.get("tags") or []
    dom = _domain(ev["url"])
    if dom not in tags:
        tags = [*tags, dom][:8]

    # dedupe by URL
    row = conn.execute(text("SELECT id FROM events WHERE url=:u"), {"u": ev["url"]}).first()
    if row:
        conn.execute(
            text("""
                UPDATE events SET
                    title=:t, description=:d, start_time=:s, location=:l, tags=:g
                WHERE id=:id
            """),
            {"t": ev["title"], "d": ev.get("description",""), "s": ev["start_time"],
             "l": ev.get("location",""), "g": json.dumps(tags), "id": row.id},
        )
        return 1
    else:
        conn.execute(
            text("""
                INSERT INTO events (id, title, description, start_time, location, tags, url)
                VALUES (:id, :t, :d, :s, :l, :g, :u)
            """),
            {"id": str(uuid.uuid4()), "t": ev["title"], "d": ev.get("description",""),
             "s": ev["start_time"], "l": ev.get("location",""), "g": json.dumps(tags), "u": ev["url"]},
        )
        return 1

# -------- Ingest modes --------
def ingest_localist_from_rss(rss_page: str) -> int:
    total = 0
    eng = _engine()
    with eng.begin() as conn:
        feeds = get_rss_links(rss_page)
        for f in feeds:
            for it in iter_rss_items(f):
                ev = parse_event_page(it["link"])
                if ev:
                    total += upsert_event(conn, ev)
                time.sleep(0.2)
    return total

def ingest_calendar_listings(listings_url: str = "https://calendar.gatech.edu/event/listings", max_links: int = 120) -> int:
    eng = _engine()
    html = _fetch(listings_url).text
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/event/" in href:
            links.append(urljoin(listings_url, href))
    # dedupe
    links = list(dict.fromkeys(links))[:max_links]

    total = 0
    with eng.begin() as conn:
        for lk in links:
            ev = parse_event_page(lk)
            if ev:
                total += upsert_event(conn, ev)
            time.sleep(0.2)
    return total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rss-page", default=None, help="Discover & ingest via RSS directory page")
    ap.add_argument("--calendar-listings", action="store_true", help="Scrape listings page for event links")
    args = ap.parse_args()

    total = 0
    if args.rss_page:
        total += ingest_localist_from_rss(args.rss_page)
    if args.calendar_listings:
        total += ingest_calendar_listings()
    print(f"Ingested: {total}")

if __name__ == "__main__":
    main()
