"""
Live Hacker News Ingestion Stream (100% Free, Zero API Keys Required).
Streams real B2B, tech, and SaaS questions from Ask HN via the official Algolia API.
Provides authentic, working news.ycombinator.com URLs and high-intent discussions.
"""

import asyncio
import logging
import urllib.request
import urllib.parse
import json
import time
from typing import List
from app.ingestion.normalizer import RedditPostEvent, clean_text, is_valid_candidate

logger = logging.getLogger("dark_social_swarm.ingestion.hn")

HN_API_BASE = "https://hn.algolia.com/api/v1/search_by_date"


def fetch_hn_posts_sync(query: str = "", tags: str = "ask_hn", limit: int = 10) -> List[RedditPostEvent]:
    """Synchronously queries Hacker News Algolia endpoint and normalizes to community events."""
    params = {"hitsPerPage": limit, "tags": tags}
    if query:
        params["query"] = query
    url = f"{HN_API_BASE}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DarkSocialSwarm/0.1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            events: List[RedditPostEvent] = []
            for hit in data.get("hits", []):
                obj_id = str(hit.get("objectID", ""))
                if not obj_id:
                    continue
                title = clean_text(hit.get("title", ""))
                raw_body = hit.get("story_text") or hit.get("comment_text") or title
                body = clean_text(raw_body)
                author = hit.get("author") or "hn_user"
                created_utc = float(hit.get("created_at_i", time.time()))
                permalink = f"https://news.ycombinator.com/item?id={obj_id}"

                event = RedditPostEvent(
                    thread_id=f"hn_{obj_id}",
                    subreddit="news.ycombinator.com",
                    title=title,
                    body=body,
                    author=author,
                    permalink=permalink,
                    created_utc=created_utc,
                )
                if is_valid_candidate(event):
                    events.append(event)
            return events
    except Exception as e:
        logger.warning(f"Error fetching live Hacker News discussions: {e}")
        return []


async def fetch_hn_posts(query: str = "", tags: str = "ask_hn", limit: int = 10) -> List[RedditPostEvent]:
    """Asynchronously fetches live Hacker News posts without blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fetch_hn_posts_sync, query, tags, limit)
