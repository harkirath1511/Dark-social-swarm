"""
Phase 4 Verification: End-to-End API & Human-in-the-Loop Resume Flow.
Verifies:
1. GET /api/feed: Paginated list of ingested posts and statuses
2. GET /api/review-queue: List of threads paused in interrupt state
3. POST /api/review/{thread_id}/submit: Submitting marketer action resumes graph to END with correct human_status
"""

import pytest
import httpx
from app.main import app
from app.core.database import init_db, get_opportunity
from app.api.dependencies import get_graph


@pytest.mark.asyncio
async def test_api_health():
    """Verify system health endpoint."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_feed_pagination():
    """Verify GET /api/feed returns paginated list of posts with total count and statuses."""
    await init_db()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Ingest a sample post
        await client.post("/api/ingest/simulate", json={
            "title": "Discussion on AI video tools",
            "body": "Need tools that don't chop sentences abruptly",
            "subreddit": "r/SaaS",
            "author": "feed_tester",
        })

        response = await client.get("/api/feed?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert "limit" in data
        assert data["limit"] == 10
        assert len(data["items"]) >= 1
        first_item = data["items"][0]
        assert "thread_id" in first_item
        assert "status" in first_item


@pytest.mark.asyncio
async def test_end_to_end_interrupt_and_resume_submit():
    """
    Phase 4 Core Verification:
    1. Start graph -> hits interrupt()
    2. Check GET /api/review-queue -> thread is paused awaiting review
    3. Call resume API POST /api/review/{thread_id}/submit with action & edited_text
    4. Verify graph transitions to END with correct human_status and final_response_text
    """
    await init_db()
    graph = get_graph()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Start graph by ingesting a high-opportunity post
        ingest_payload = {
            "title": "Looking for a workflow to turn 1hr podcast interviews into viral shorts",
            "body": "Most tools cut off sentences right in the middle. Need something with semantic boundary detection.",
            "subreddit": "r/SaaS",
            "author": "creator_alex",
        }
        ingest_resp = await client.post("/api/ingest/simulate", json=ingest_payload)
        assert ingest_resp.status_code == 200
        thread_id = ingest_resp.json()["thread_id"]
        assert thread_id.startswith("t3_")

        # Verify graph halted at interrupt
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = await graph.aget_state(config)
        assert "human_review" in state_snapshot.next or (state_snapshot.tasks and state_snapshot.tasks[0].name == "human_review")

        # 2. Check GET /api/review-queue
        queue_resp = await client.get("/api/review-queue")
        assert queue_resp.status_code == 200
        queue_data = queue_resp.json()
        assert queue_data["count"] >= 1
        queue_ids = [opp["thread_id"] for opp in queue_data["queue"]]
        assert thread_id in queue_ids

        # 3. Call resume API POST /api/review/{thread_id}/submit with edited text
        custom_edit = "The cleanest fix is using token-level boundary timestamps so cuts strictly follow punctuation."
        submit_payload = {
            "action": "edited",
            "edited_text": custom_edit,
        }
        submit_resp = await client.post(f"/api/review/{thread_id}/submit", json=submit_payload)
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert submit_data["status"] in ("resumed", "resumed_fallback")
        assert submit_data["human_status"] == "edited"
        assert submit_data["final_response_text"] == custom_edit

        # 4. Verify graph transitioned to END (no pending tasks remaining)
        final_state_snapshot = await graph.aget_state(config)
        assert len(final_state_snapshot.next) == 0  # Completed at END node

        # 5. Verify database record updated
        db_lead = await get_opportunity(thread_id)
        assert db_lead is not None
        assert db_lead["status"] == "EDITED"
        assert db_lead["human_status"] == "edited"
        assert db_lead["final_response_text"] == custom_edit

        # 6. Verify thread is removed from review-queue
        queue_after = await client.get("/api/review-queue")
        assert queue_after.status_code == 200
        queue_after_ids = [opp["thread_id"] for opp in queue_after.json()["queue"]]
        assert thread_id not in queue_after_ids
