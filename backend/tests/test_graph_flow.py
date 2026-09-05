"""
Phase 3 Verification: Multi-Agent Swarm Logic & LangGraph StateGraph Execution.
Verifies:
1. Analyst, Strategist, Drafter, and Critic nodes
2. Conditional routing: drop (< 40) vs engage (>= 40)
3. Critic revision loopback on policy violation
4. Execution pause at Human Review Node via interrupt() and resumption via Command(resume=...)
"""

import uuid
import pytest
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from app.core.database import init_db
from app.swarm.state import SwarmState
from app.swarm.agents.critic import programmatic_guardrails_check
from app.swarm.graph import (
    build_swarm_graph,
    compile_swarm_graph,
    route_after_strategist,
    route_after_critic,
)


@pytest.mark.asyncio
async def test_critic_guardrails_detection():
    """Verify that programmatic Guardrails catch link drops and promotional CTAs."""
    # 1. External link violation
    dirty_draft_link = "Check out our video tool at https://myvideotool.io for automated clipping."
    res1 = programmatic_guardrails_check(dirty_draft_link)
    assert res1 is not None
    assert res1.critic_passed is False
    assert res1.violation_category == "excessive_promotion"
    assert "URL" in res1.critic_feedback

    # 2. Aggressive sales CTA violation
    dirty_draft_cta = "We offer a solution! Sign up now and use promo code 50% off."
    res2 = programmatic_guardrails_check(dirty_draft_cta)
    assert res2 is not None
    assert res2.critic_passed is False
    assert res2.violation_category == "excessive_promotion"

    # 3. Clean value-first reply passes
    clean_draft = (
        "The core reason this happens is silence thresholding. "
        "A better approach is token-level timestamp alignment so cuts only happen at punctuation."
    )
    res3 = programmatic_guardrails_check(clean_draft)
    assert res3 is None


def test_conditional_routing_logic():
    """Verify routing decisions after Strategist, Sensitive Gate, and Critic."""
    from app.swarm.graph import route_after_sensitive_gate

    # Strategist: Low score (< 40) drops to END
    low_state: SwarmState = {"opportunity_score": 25, "engagement_decision": "do_not_engage"}
    assert route_after_strategist(low_state) == "__end__"

    # Strategist: High score (>= 40) proceeds to Sensitive Gate
    high_state: SwarmState = {"opportunity_score": 85, "engagement_decision": "engage"}
    assert route_after_strategist(high_state) == "sensitive_gate"

    # Sensitive Gate: Normal topic proceeds to Drafter
    normal_state: SwarmState = {"sensitive_topic": False}
    assert route_after_sensitive_gate(normal_state) == "drafter"

    # Sensitive Gate: Sensitive topic bypasses Drafter and routes straight to Human Review
    sensitive_state: SwarmState = {"sensitive_topic": True}
    assert route_after_sensitive_gate(sensitive_state) == "human_review"

    # Critic: Failed and iteration < 2 loops back to Drafter
    fail_state: SwarmState = {"critic_passed": False, "draft_iteration": 1}
    assert route_after_critic(fail_state) == "drafter"

    # Critic: Passed proceeds to Human Review
    pass_state: SwarmState = {"critic_passed": True, "draft_iteration": 1}
    assert route_after_critic(pass_state) == "human_review"

    # Critic: Failed but reached max iterations proceeds to Human Review with flags
    exhausted_state: SwarmState = {"critic_passed": False, "draft_iteration": 2}
    assert route_after_critic(exhausted_state) == "human_review"


@pytest.mark.asyncio
async def test_graph_discard_flow():
    """Verify that spam/low-intent posts are dropped at Strategist without triggering Drafter."""
    await init_db()
    checkpointer = MemorySaver()
    graph = compile_swarm_graph(checkpointer=checkpointer)

    thread_id = f"t3_spam_{uuid.uuid4().hex[:8]}"
    initial_state: SwarmState = {
        "platform": "reddit",
        "thread_id": thread_id,
        "subreddit": "r/marketing",
        "title": "Cheap SEO backlink package discount code 50% off",
        "body": "Buy our promotional links now",
        "author": "spammer",
        "permalink": f"https://reddit.com/r/marketing/{thread_id}",
    }

    config = {"configurable": {"thread_id": thread_id}}
    final_state = await graph.ainvoke(initial_state, config=config)

    # Should be dropped at Strategist
    assert final_state["opportunity_score"] < 40
    assert final_state["engagement_decision"] == "do_not_engage"
    assert "proposed_draft" not in final_state or final_state.get("proposed_draft") is None


@pytest.mark.asyncio
async def test_graph_interrupt_and_resume_flow():
    """Verify that high-scoring opportunities pause at human_review_node and resume via Command."""
    await init_db()
    checkpointer = MemorySaver()
    graph = compile_swarm_graph(checkpointer=checkpointer)

    thread_id = f"t3_opp_{uuid.uuid4().hex[:8]}"
    initial_state: SwarmState = {
        "platform": "reddit",
        "thread_id": thread_id,
        "subreddit": "r/SaaS",
        "title": "I've tried three tools for turning long videos into clips. Which one actually works?",
        "body": "Most automated tools cut off sentences right in the middle or pick arbitrary highlights.",
        "author": "creator_dan99",
        "permalink": f"https://reddit.com/r/SaaS/{thread_id}",
    }

    config = {"configurable": {"thread_id": thread_id}}

    # 1. Run graph - it must execute Analyst -> Strategist -> Drafter -> Critic -> interrupt()
    interrupted_result = await graph.ainvoke(initial_state, config=config)

    # 2. Verify graph paused at human_review with full pipeline state
    state_snapshot = await graph.aget_state(config)
    assert len(state_snapshot.tasks) > 0
    assert "human_review" in state_snapshot.next or state_snapshot.tasks[0].name == "human_review"

    # Stage 1: Analyst output verified
    assert "extracted_problem" in state_snapshot.values
    assert len(state_snapshot.values["extracted_problem"]) > 0
    assert state_snapshot.values["user_intent"] in ("recommendation_seeking", "alternative_seeking", "high", "medium")
    assert len(state_snapshot.values["evidence_quote"]) > 0

    # Stage 2: Strategist output verified
    assert state_snapshot.values["opportunity_score"] >= 40
    assert state_snapshot.values["engagement_decision"] in ("engage", "maybe_engage")
    assert len(state_snapshot.values["strategic_reasoning"]) > 0

    # Stage 3: Drafter output verified
    assert len(state_snapshot.values["proposed_draft"]) > 0
    assert state_snapshot.values["draft_iteration"] >= 1

    # Stage 4: Critic output verified
    assert state_snapshot.values["critic_passed"] is True

    # Stage 5: Interrupt yielded state verified for human input
    if hasattr(state_snapshot.tasks[0], "interrupts") and state_snapshot.tasks[0].interrupts:
        yielded_payload = state_snapshot.tasks[0].interrupts[0].value
        assert yielded_payload["thread_id"] == thread_id
        assert yielded_payload["extracted_problem"] == state_snapshot.values["extracted_problem"]
        assert yielded_payload["opportunity_score"] == state_snapshot.values["opportunity_score"]
        assert yielded_payload["proposed_draft"] == state_snapshot.values["proposed_draft"]

    # 3. Resume the graph using Command(resume=...)
    resumed_result = await graph.ainvoke(
        Command(resume={
            "action": "approved",
            "final_response_text": state_snapshot.values["proposed_draft"],
        }),
        config=config,
    )

    # 4. Verify graph completed to END with marketer triage recorded
    final_snapshot = await graph.aget_state(config)
    assert len(final_snapshot.next) == 0  # Graph finished (at END)
    assert resumed_result["human_status"] == "approved"
    assert resumed_result["final_response_text"] == state_snapshot.values["proposed_draft"]
