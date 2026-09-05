"""
Delta Upgrade Verification Suite.
Directly verifies the 3 core scenarios specified in the directive:
1. Unbranded Problem Detection:
   Thread "I've tried three tools for turning long videos into clips. Which one actually works?"
   passes discovery with brand_mentioned = False and scores >= 80 opportunity.
2. Sensitive Gate Trigger:
   Thread regarding a personal medical or legal crisis routes directly to human_review without invoking drafter.
3. Critic Re-draft Loop:
   A draft containing astroturfing triggers critic_passed = False, updates critic_feedback, loops back to drafter, and increments draft_iteration.
4. Structured Human Rejection:
   Marketer rejection with structured reason ('wrong_community') persists to SQLite.
"""

import uuid
import pytest
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from app.core.database import init_db, get_opportunity
from app.ingestion.discovery import evaluate_candidate_discovery
from app.ingestion.community_rules import get_community_context, get_community_rules
from app.swarm.state import SwarmState
from app.swarm.agents.analyst import analyst_node
from app.swarm.agents.strategist import strategist_node
from app.swarm.agents.critic import critic_node, programmatic_guardrails_check
from app.swarm.agents.drafter import drafter_node
from app.swarm.graph import compile_swarm_graph


@pytest.mark.asyncio
async def test_scenario_1_unbranded_problem_detection():
    """
    Scenario 1: Unbranded Problem Detection.
    Thread: "I've tried three tools for turning long videos into clips. Which one actually works?"
    - Must pass candidate discovery pre-filter (score >= 0.50) without brand dependencies.
    - Analyst must extract problem and set brand_mentioned = False.
    - Strategist must assign opportunity_score >= 80 and engagement_decision = 'engage'.
    """
    await init_db()
    title = "I've tried three tools for turning long videos into clips. Which one actually works?"
    body = "Most automated tools cut off sentences right in the middle or pick arbitrary highlights. Looking for something that respects sentence boundaries."

    # 1. Candidate Discovery Pre-Filter
    passed, discovery_score = evaluate_candidate_discovery(f"{title}\n{body}")
    assert passed is True, f"Expected discovery to pass, got score: {discovery_score}"
    assert discovery_score >= 0.50

    thread_id = f"t3_unbranded_{uuid.uuid4().hex[:8]}"
    state: SwarmState = {
        "platform": "reddit",
        "thread_id": thread_id,
        "community_id": "r/videoediting",
        "subreddit": "r/videoediting",
        "title": title,
        "body": body,
        "author": "video_creator_tim",
        "permalink": f"https://reddit.com/r/videoediting/comments/{thread_id}",
        "discovery_passed": passed,
        "discovery_score": discovery_score,
    }

    # 2. Analyst Execution
    analyst_output = await analyst_node(state)
    state.update(analyst_output)

    assert state["brand_mentioned"] is False, "Brand should be False for unbranded discussion"
    assert state["mentioned_brands"] == []
    assert state["user_intent"] in ("recommendation_seeking", "alternative_seeking")
    assert len(state["evidence"]) >= 1
    assert len(state["evidence_quote"]) > 0

    # 3. Strategist Execution
    strategist_output = await strategist_node(state)
    state.update(strategist_output)

    assert state["opportunity_score"] >= 80, f"Expected score >= 80, got {state['opportunity_score']}"
    assert state["engagement_decision"] == "engage"
    assert state["relevance_score"] >= 80
    assert state["intent_strength_score"] >= 85
    assert "Why this user" in state["strategic_reasoning"]


@pytest.mark.asyncio
async def test_scenario_2_sensitive_gate_trigger():
    """
    Scenario 2: Sensitive Gate Trigger.
    Thread regarding personal medical or legal crisis:
    - Passes Strategist gate (if qualified)
    - Triggers Sensitive Topic Gate (sensitive_topic = True)
    - Bypasses Drafter completely
    - Routes directly to Human Review Node
    """
    await init_db()
    checkpointer = MemorySaver()
    graph = compile_swarm_graph(checkpointer=checkpointer)

    thread_id = f"t3_crisis_{uuid.uuid4().hex[:8]}"
    initial_state: SwarmState = {
        "platform": "reddit",
        "thread_id": thread_id,
        "community_id": "r/smallbusiness",
        "subreddit": "r/smallbusiness",
        "title": "Emergency help: Our business partner had a severe medical crisis and now we are facing a major lawsuit",
        "body": "Looking for tools or advice on how to preserve company records during active litigation while our partner is in the hospital.",
        "author": "distressed_owner",
        "permalink": f"https://reddit.com/r/smallbusiness/comments/{thread_id}",
    }

    config = {"configurable": {"thread_id": thread_id}}

    # Run graph until interrupt
    await graph.ainvoke(initial_state, config=config)

    # Inspect paused state snapshot
    snapshot = await graph.aget_state(config)

    # 1. Must pause at human_review
    assert len(snapshot.tasks) > 0
    assert "human_review" in snapshot.next or snapshot.tasks[0].name == "human_review"

    # 2. Sensitive flag MUST be True
    assert snapshot.values.get("sensitive_topic") is True
    assert snapshot.values.get("sensitive_topic_reason") is not None
    assert "Sensitive topic detected" in snapshot.values["sensitive_topic_reason"]

    # 3. Drafter MUST be completely bypassed (draft_iteration == 0 and no proposed_draft generated by Drafter)
    assert snapshot.values.get("draft_iteration", 0) == 0
    assert snapshot.values.get("proposed_draft") in (None, "")


@pytest.mark.asyncio
async def test_scenario_3_critic_redraft_loop():
    """
    Scenario 3: Critic Re-draft Loop.
    A draft containing astroturfing triggers critic_passed = False, updates critic_feedback,
    loops back to drafter, and increments draft_iteration.
    """
    await init_db()

    thread_id = f"t3_astroturf_{uuid.uuid4().hex[:8]}"

    # 1. Draft with deceptive customer persona (astroturfing)
    astroturfing_draft = (
        "As an unaffiliated user, I stumbled across this tool and it saved my life! "
        "It cuts podcasts automatically without any bugs."
    )

    # Verify programmatic guardrail directly
    guardrail_res = programmatic_guardrails_check(astroturfing_draft)
    assert guardrail_res is not None
    assert guardrail_res.critic_passed is False
    assert guardrail_res.violation_category == "astroturfing"
    assert "astroturfing" in guardrail_res.critic_feedback.lower()

    # 2. Execute Critic Node with this draft
    critic_input_state: SwarmState = {
        "thread_id": thread_id,
        "community_id": "r/SaaS",
        "title": "Which video editing tool actually clips podcasts?",
        "extracted_problem": "Need tools that don't chop sentences abruptly",
        "evidence_quote": "Which video editing tool actually clips podcasts?",
        "proposed_draft": astroturfing_draft,
        "draft_iteration": 1,
    }

    critic_output = await critic_node(critic_input_state)
    assert critic_output["critic_passed"] is False
    assert critic_output["violation_category"] == "astroturfing"
    assert critic_output["critic_feedback"] is not None

    # 3. Simulate loopback to Drafter with the feedback
    drafter_input_state = {**critic_input_state, **critic_output}
    redraft_output = await drafter_node(drafter_input_state)

    # 4. Drafter increments iteration count
    assert redraft_output["draft_iteration"] == 2
    # 5. Cleaned draft does not contain astroturfing phrase
    assert "as an unaffiliated user" not in redraft_output["proposed_draft"].lower()
    assert "i stumbled across" not in redraft_output["proposed_draft"].lower()


@pytest.mark.asyncio
async def test_scenario_4_structured_human_rejection_persistence():
    """
    Verify that marketer rejection with a structured rejection reason
    ('wrong_community') persists to SQLite and updates thread status to REJECTED.
    """
    await init_db()
    checkpointer = MemorySaver()
    graph = compile_swarm_graph(checkpointer=checkpointer)

    thread_id = f"t3_rejection_{uuid.uuid4().hex[:8]}"
    initial_state: SwarmState = {
        "platform": "reddit",
        "thread_id": thread_id,
        "community_id": "r/startups",
        "subreddit": "r/startups",
        "title": "Need CRM advice for tracking B2B leads",
        "body": "Manual data entry is taking too long for our sales team.",
        "author": "founder_john",
        "permalink": f"https://reddit.com/r/startups/comments/{thread_id}",
    }

    config = {"configurable": {"thread_id": thread_id}}

    # Run to interrupt
    await graph.ainvoke(initial_state, config=config)

    # Resume with structured rejection reason
    resumed_result = await graph.ainvoke(
        Command(resume={
            "action": "rejected",
            "rejection_reason": "wrong_community",
        }),
        config=config,
    )

    assert resumed_result["human_status"] == "rejected"
    assert resumed_result["rejection_reason"] == "wrong_community"

    # Verify SQLite persistence
    record = await get_opportunity(thread_id)
    assert record is not None
    assert record["status"] == "REJECTED"
    assert record["human_status"] == "rejected"
    assert record["rejection_reason"] == "wrong_community"


def test_community_norms_registry():
    """Verify community norms lookup table."""
    webdev_context = get_community_context("r/webdev")
    assert "extreme" in webdev_context.lower()
    assert "zero_tolerance" in webdev_context.lower()

    saas_rules = get_community_rules("r/SaaS")
    assert saas_rules["promo_tolerance"] == "moderate"
    assert saas_rules["fit_modifier"] >= 1.0
