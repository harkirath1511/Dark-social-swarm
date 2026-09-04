"""
Phase 1 Verification: SwarmState serialization and deserialization with Pydantic.
"""

import json
import pytest
from pydantic import ValidationError
from app.swarm.state import (
    SwarmState,
    SwarmStateModel,
    AnalystResult,
    StrategistResult,
    DrafterResult,
    CriticResult,
)


def test_swarm_state_full_serialization():
    """Verify that a complete SwarmState serializes to and deserializes from JSON properly."""
    raw_state_data: SwarmState = {
        "platform": "reddit",
        "thread_id": "t3_1h9k2z8",
        "subreddit": "r/SaaS",
        "title": "I've tried three tools for turning long videos into clips. Which one actually works?",
        "body": "Most automated tools cut off sentences right in the middle or pick arbitrary highlights that don't make sense without context.",
        "author": "creator_dan99",
        "permalink": "https://reddit.com/r/SaaS/comments/1h9k2z8",
        "extracted_problem": "Video clipping tools cut off sentences mid-speech and miss semantic boundaries.",
        "user_intent": "high",
        "evidence_quote": "Most automated tools cut off sentences right in the middle or pick arbitrary highlights",
        "opportunity_score": 88,
        "engagement_decision": "engage",
        "strategic_reasoning": "Direct problem fit with video repurposing workflow, high commercial urgency.",
        "proposed_draft": "The core issue with clip generators is silence thresholding rather than transcript boundary analysis.",
        "draft_iteration": 1,
        "critic_passed": True,
        "violation_category": None,
        "critic_feedback": "Passed value-first and zero-plug checks.",
        "human_status": "approved",
        "final_response_text": "The core issue with clip generators is silence thresholding rather than transcript boundary analysis.",
    }

    # 1. Instantiate Pydantic Model from dict
    model = SwarmStateModel(**raw_state_data)
    assert model.thread_id == "t3_1h9k2z8"
    assert model.opportunity_score == 88
    assert model.engagement_decision == "engage"
    assert model.critic_passed is True
    assert model.human_status == "approved"

    # 2. Serialize to JSON string
    json_str = model.model_dump_json()
    assert isinstance(json_str, str)
    assert "t3_1h9k2z8" in json_str

    # 3. Deserialize from JSON string back into Pydantic model
    deserialized = SwarmStateModel.model_validate_json(json_str)
    assert deserialized.thread_id == model.thread_id
    assert deserialized.extracted_problem == model.extracted_problem
    assert deserialized.opportunity_score == model.opportunity_score
    assert deserialized.evidence_quote == model.evidence_quote

    # 4. Dump back to dict and verify compatibility with SwarmState TypedDict
    dumped_dict = deserialized.model_dump()
    assert dumped_dict["platform"] == "reddit"
    assert dumped_dict["opportunity_score"] == 88


def test_swarm_state_partial_initialization():
    """Verify that an early-stage state (only input context) is valid."""
    initial_dict = {
        "platform": "reddit",
        "thread_id": "t3_fresh_post",
        "subreddit": "r/startups",
        "title": "Need CRM advice",
        "body": "HubSpot is too heavy for our 3-person team.",
        "author": "founder1",
        "permalink": "https://reddit.com/r/startups/comments/fresh",
    }

    model = SwarmStateModel(**initial_dict)
    assert model.thread_id == "t3_fresh_post"
    assert model.draft_iteration == 0
    assert model.extracted_problem is None
    assert model.opportunity_score is None
    assert model.critic_passed is None
    assert model.human_status is None


def test_swarm_state_constraint_validation():
    """Verify validation errors on invalid values."""
    # Test invalid opportunity_score (> 100)
    with pytest.raises(ValidationError):
        SwarmStateModel(
            thread_id="t3_invalid",
            subreddit="r/SaaS",
            title="Title",
            permalink="https://reddit.com/r/SaaS/invalid",
            opportunity_score=150,  # exceeds 100
        )

    # Test invalid engagement_decision literal
    with pytest.raises(ValidationError):
        SwarmStateModel(
            thread_id="t3_invalid",
            subreddit="r/SaaS",
            title="Title",
            permalink="https://reddit.com/r/SaaS/invalid",
            engagement_decision="definitely_buy_now",  # invalid literal
        )


def test_agent_structured_contracts():
    """Verify individual node output contracts."""
    analyst = AnalystResult(
        extracted_problem="HubSpot friction",
        user_intent="high",
        evidence_quote="HubSpot is too heavy for our 3-person team.",
    )
    assert analyst.user_intent == "high"

    strategist = StrategistResult(
        opportunity_score=75,
        engagement_decision="engage",
        strategic_reasoning="Strong resonance with CRM pain points.",
    )
    assert strategist.opportunity_score == 75

    drafter = DrafterResult(
        proposed_draft="Consider using a webhook bridge to Notion or Airtable."
    )
    assert "webhook" in drafter.proposed_draft

    critic = CriticResult(
        critic_passed=True,
        violation_category=None,
        critic_feedback=None,
    )
    assert critic.critic_passed is True
