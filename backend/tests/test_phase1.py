"""
Phase 1 Unit Tests: Normalizer, Lead Database (WAL), and SwarmState.
"""

import os
import pytest
import asyncio
from app.ingestion.normalizer import normalize_submission, is_valid_candidate, RedditPostEvent
from app.core.database import init_db, save_raw_post, get_opportunity, update_opportunity_status
from app.swarm.state import AnalystResult, StrategistResult, CriticResult, SwarmState


@pytest.mark.asyncio
async def test_normalizer_dict():
    raw_data = {
        "id": "1h9k2z8",
        "subreddit": "SaaS",
        "title": "   I've tried three tools for turning long videos into clips. Which one actually works?   ",
        "selftext": "Most automated tools cut off sentences right in the middle...\n\n\n\nContext matters.",
        "author": "creator_dan99",
        "permalink": "/r/SaaS/comments/1h9k2z8",
        "created_utc": 1725500000.0,
    }
    event = normalize_submission(raw_data)
    assert event.thread_id == "t3_1h9k2z8"
    assert event.subreddit == "r/SaaS"
    assert event.title.startswith("I've tried")
    assert not event.title.endswith(" ")
    assert "\n\n\n" not in event.body
    assert event.permalink == "https://reddit.com/r/SaaS/comments/1h9k2z8"
    assert is_valid_candidate(event) is True


@pytest.mark.asyncio
async def test_normalizer_invalid_posts():
    spam_post = RedditPostEvent(
        thread_id="t3_bad1",
        subreddit="r/SaaS",
        title="Hi",  # too short
        body="Buy this",
        author="bot",
        permalink="https://reddit.com/r/SaaS/bad1",
        created_utc=1725500000.0,
    )
    assert is_valid_candidate(spam_post) is False

    deleted_author = RedditPostEvent(
        thread_id="t3_bad2",
        subreddit="r/SaaS",
        title="Valid title with plenty of words",
        body="Some text here",
        author="[deleted]",
        permalink="https://reddit.com/r/SaaS/bad2",
        created_utc=1725500000.0,
    )
    assert is_valid_candidate(deleted_author) is False


@pytest.mark.asyncio
async def test_database_lifecycle():
    await init_db()
    import uuid
    test_id = f"t3_test_{uuid.uuid4().hex[:8]}"
    
    # Insert post
    row = await save_raw_post(
        thread_id=test_id,
        subreddit="r/SaaS",
        title="Test Opportunity Post",
        body="Looking for better CRM alternatives",
        author="tester",
        permalink=f"https://reddit.com/r/SaaS/{test_id}",
        created_utc=1725500000.0,
    )
    assert row["thread_id"] == test_id
    assert row["status"] == "DISCOVERED"

    # Verify retrieval
    retrieved = await get_opportunity(test_id)
    assert retrieved is not None
    assert retrieved["title"] == "Test Opportunity Post"

    # Update status
    await update_opportunity_status(test_id, "PROCESSING")
    updated = await get_opportunity(test_id)
    assert updated["status"] == "PROCESSING"


def test_swarm_state_contract():
    analyst_res = AnalystResult(
        extracted_problem="Struggling with video editing cuts",
        user_intent="high",
        evidence_quote="Most automated tools cut off sentences right in the middle",
    )
    assert analyst_res.user_intent == "high"

    strategist_res = StrategistResult(
        opportunity_score=85,
        engagement_decision="engage",
        strategic_reasoning="High buying intent and strong community fit",
    )
    assert strategist_res.opportunity_score >= 40
    assert strategist_res.engagement_decision == "engage"

    critic_res = CriticResult(
        critic_passed=True,
        violation_category=None,
        critic_feedback=None,
    )
    assert critic_res.critic_passed is True
