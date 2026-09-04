"""
Unit tests for Reddit Ingestion Stream Daemon & Queue.
"""

import pytest
import asyncio
from app.ingestion.listener import RedditListener
from app.ingestion.normalizer import RedditPostEvent
from app.core.database import init_db, get_opportunity


@pytest.mark.asyncio
async def test_listener_queue_push():
    await init_db()
    queue = asyncio.Queue()
    listener = RedditListener(queue)

    # Start daemon
    listener.start()

    # Wait for at least 2 synthetic events to be ingested and persisted
    events = []
    for _ in range(2):
        event: RedditPostEvent = await asyncio.wait_for(queue.get(), timeout=5.0)
        events.append(event)
        queue.task_done()

    await listener.stop()

    assert len(events) >= 2
    first = events[0]
    assert first.thread_id.startswith("t3_")
    assert first.subreddit in ("r/SaaS", "r/startups", "r/Entrepreneur")

    # Verify post was saved in SQLite
    saved = await get_opportunity(first.thread_id)
    assert saved is not None
    assert saved["thread_id"] == first.thread_id
    assert saved["status"] == "DISCOVERED"
