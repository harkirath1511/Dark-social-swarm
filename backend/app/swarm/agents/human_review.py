"""
Human Review Node with native LangGraph interrupt().
Adapted from KirtiJha/langgraph-interrupt-workflow-template:
Pauses execution state until a marketer resumes via REST API Command(resume=...).
"""

import logging
from typing import Dict, Any
from langgraph.types import interrupt

from app.core.database import record_human_triage
from app.swarm.state import SwarmState

logger = logging.getLogger("dark_social_swarm.agents.human_review")


async def human_review_node(state: SwarmState) -> Dict[str, Any]:
    """
    Human Review Node.
    Invokes interrupt() to freeze execution in the checkpointer.
    Resumes when marketer sends approval/edit/rejection payload.
    """
    thread_id = state.get("thread_id", "")
    subreddit = state.get("subreddit", "")
    title = state.get("title", "")
    proposed_draft = state.get("proposed_draft", "")
    opportunity_score = state.get("opportunity_score", 0)
    evidence_quote = state.get("evidence_quote", "")
    critic_passed = state.get("critic_passed", False)
    violation_category = state.get("violation_category")

    logger.info(f"[HumanReviewNode] Pausing execution on thread {thread_id} via interrupt()...")

    full_payload = {
        "platform": state.get("platform", "reddit"),
        "thread_id": thread_id,
        "subreddit": subreddit,
        "title": title,
        "body": state.get("body", ""),
        "author": state.get("author", "[deleted]"),
        "permalink": state.get("permalink", ""),
        "extracted_problem": state.get("extracted_problem", ""),
        "user_intent": state.get("user_intent", "medium"),
        "evidence_quote": evidence_quote,
        "opportunity_score": opportunity_score,
        "engagement_decision": state.get("engagement_decision", "engage"),
        "strategic_reasoning": state.get("strategic_reasoning", ""),
        "proposed_draft": proposed_draft,
        "draft_iteration": state.get("draft_iteration", 1),
        "critic_passed": critic_passed,
        "violation_category": violation_category,
        "critic_feedback": state.get("critic_feedback"),
    }

    # The interrupt() call halts graph execution, saves state to checkpointer,
    # and yields the full context payload for the UI.
    decision = interrupt(full_payload)

    # Validate resumed payload
    human_status = decision.get("action", "approved").lower() if isinstance(decision, dict) else "approved"
    final_text = decision.get("final_response_text", proposed_draft) if isinstance(decision, dict) else proposed_draft

    logger.info(f"[HumanReviewNode] Resumed thread {thread_id} with decision: {human_status}")

    # Persist final decision in SQLite
    await record_human_triage(
        thread_id=thread_id,
        human_status=human_status,
        final_response_text=final_text,
    )

    return {
        "human_status": human_status,
        "final_response_text": final_text,
    }
