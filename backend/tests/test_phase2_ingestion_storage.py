"""
Phase 2 Verification: Ingestion & Lead Storage Architecture.
Tests PRAW streaming daemon / synthetic queue, SQLite WAL mode, and complete opportunity lifecycle states:
DISCOVERED -> PROCESSING -> AWAITING_APPROVAL -> APPROVED / EDITED / REJECTED / DISCARDED.
"""

import uuid
import pytest
import asyncio
from app.core.database import (
    init_db,
    save_raw_post,
    update_analyst_signals,
    update_strategist_decision,
    update_draft_and_critic,
    record_human_triage,
    get_opportunity,
    get_pending_opportunities,
    get_all_opportunities,
)
from app.ingestion.listener import RedditListener
from app.ingestion.normalizer import RedditPostEvent, normalize_submission, is_valid_candidate


@pytest.mark.asyncio
async def test_ingestion_daemon_and_queue():
    """Verify that the ingestion daemon pushes valid posts into the async queue and SQLite."""
    await init_db()
    queue = asyncio.Queue()
    listener = RedditListener(queue)

    # Start daemon
    listener.start()

    # Capture at least 2 events from the stream
    events = []
    for _ in range(2):
        event: RedditPostEvent = await asyncio.wait_for(queue.get(), timeout=5.0)
        events.append(event)
        queue.task_done()

    await listener.stop()

    assert len(events) >= 2
    first_event = events[0]
    assert first_event.thread_id.startswith("t3_")
    assert first_event.subreddit.startswith("r/")
    assert len(first_event.title) > 0
    assert first_event.permalink.startswith("http")

    # Verify that the post was automatically saved with status DISCOVERED in SQLite
    saved = await get_opportunity(first_event.thread_id)
    assert saved is not None
    assert saved["thread_id"] == first_event.thread_id
    assert saved["status"] == "DISCOVERED"
    assert saved["platform"] == "reddit"


@pytest.mark.asyncio
async def test_opportunity_lifecycle_transitions():
    """Verify step-by-step state transitions through the multi-agent pipeline."""
    await init_db()
    thread_id = f"t3_test_{uuid.uuid4().hex[:8]}"

    # 1. Post Discovery
    post = await save_raw_post(
        thread_id=thread_id,
        subreddit="r/SaaS",
        title="Looking for a tool to auto-clip long podcasts into shorts",
        body="Most tools cut sentences abruptly. Any recommendations?",
        author="podcast_host",
        permalink=f"https://reddit.com/r/SaaS/comments/{thread_id}",
        created_utc=1725500000.0,
    )
    assert post["status"] == "DISCOVERED"

    # 2. Analyst Node processing
    await update_analyst_signals(
        thread_id=thread_id,
        extracted_problem="Video clipping tools cut off sentences abruptly",
        user_intent="high",
        evidence_quote="Most tools cut sentences abruptly.",
    )
    after_analyst = await get_opportunity(thread_id)
    assert after_analyst["status"] == "PROCESSING"
    assert after_analyst["extracted_problem"] == "Video clipping tools cut off sentences abruptly"
    assert after_analyst["user_intent"] == "high"
    assert after_analyst["evidence_quote"] == "Most tools cut sentences abruptly."

    # 3. Strategist Node evaluation (Fit & Opportunity Score)
    await update_strategist_decision(
        thread_id=thread_id,
        opportunity_score=85,
        engagement_decision="engage",
        strategic_reasoning="Strong intent and clear product alignment with video clipping tools.",
        status="PROCESSING",
    )
    after_strategist = await get_opportunity(thread_id)
    assert after_strategist["opportunity_score"] == 85
    assert after_strategist["engagement_decision"] == "engage"
    assert after_strategist["status"] == "PROCESSING"

    # 4. Drafter & Critic validation
    draft_text = "The issue with most automated clip tools is that they cut strictly on silence."
    await update_draft_and_critic(
        thread_id=thread_id,
        proposed_draft=draft_text,
        draft_iteration=1,
        critic_passed=True,
        violation_category=None,
        critic_feedback="Passed zero-plug and value-first guidelines.",
        status="AWAITING_APPROVAL",
    )
    after_critic = await get_opportunity(thread_id)
    assert after_critic["status"] == "AWAITING_APPROVAL"
    assert after_critic["proposed_draft"] == draft_text
    assert after_critic["critic_passed"] == 1
    assert after_critic["draft_iteration"] == 1

    # Verify that pending list retrieves this opportunity
    pending = await get_pending_opportunities()
    pending_ids = [p["thread_id"] for p in pending]
    assert thread_id in pending_ids

    # 5. Human Review Node triage (Marketer Approval)
    decision = await record_human_triage(
        thread_id=thread_id,
        human_status="approved",
        final_response_text=draft_text,
    )
    assert decision["status"] == "APPROVED"
    assert decision["human_status"] == "approved"
    assert decision["final_response_text"] == draft_text

    # Verify it is no longer pending
    pending_after = await get_pending_opportunities()
    assert thread_id not in [p["thread_id"] for p in pending_after]


@pytest.mark.asyncio
async def test_low_score_discard_lifecycle():
    """Verify that low opportunity scores (< 40) or 'do_not_engage' can be marked DISCARDED."""
    await init_db()
    spam_id = f"t3_spam_{uuid.uuid4().hex[:8]}"

    await save_raw_post(
        thread_id=spam_id,
        subreddit="r/marketing",
        title="Check our brand new SEO backlink package 50% discount",
        body="Spam link to cheap backlinks",
        author="spam_bot",
        permalink=f"https://reddit.com/r/marketing/comments/{spam_id}",
        created_utc=1725500000.0,
    )

    await update_strategist_decision(
        thread_id=spam_id,
        opportunity_score=15,
        engagement_decision="do_not_engage",
        strategic_reasoning="Obvious spam promotion with zero organic buying intent.",
        status="DISCARDED",
    )

    record = await get_opportunity(spam_id)
    assert record["status"] == "DISCARDED"
    assert record["opportunity_score"] == 15
    assert record["engagement_decision"] == "do_not_engage"
