"""
News fetcher — fetches Indian market news via RSS/API.
Uses Economic Times and Moneycontrol RSS feeds (no API key required).
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
import urllib.error
from database import get_db

logger = logging.getLogger(__name__)

NEWS_FEEDS = [
    ("Economic Times", "https://economictimes.indiatimes.com/markets/rss.cms"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/latestnews.xml"),
]


def fetch_news():
    """Fetch news from RSS feeds and cache in DB."""
    all_news = []

    for source, url in NEWS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SwingTraderPro/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
            root = ET.fromstring(content)
            items = root.findall(".//item")[:15]

            for item in items:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                desc = (item.findtext("description") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                # Strip HTML tags from description
                import re
                desc = re.sub(r"<[^>]+>", "", desc)[:300]

                if title:
                    all_news.append({
                        "title": title,
                        "summary": desc,
                        "url": link,
                        "source": source,
                        "published_at": pub_date
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch news from {source}: {e}")

    if all_news:
        db = get_db()
        db.execute("DELETE FROM news_cache")
        for n in all_news:
            db.execute("""
                INSERT INTO news_cache (title, summary, url, source, published_at)
                VALUES (?,?,?,?,?)
            """, (n["title"], n["summary"], n["url"], n["source"], n["published_at"]))
        db.commit()
        db.close()
        logger.info(f"Fetched and cached {len(all_news)} news items")

    return all_news


def get_cached_news(limit: int = 20):
    """Return cached news from DB."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM news_cache ORDER BY fetched_at DESC LIMIT ?", (limit,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]
