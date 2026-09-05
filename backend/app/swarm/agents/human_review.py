"""
Human Review Node with native LangGraph interrupt().
Differences 13, 14:
Pauses execution state until a marketer resumes via REST API Command(resume=...).
Captures approved text, in-place edits, or structured rejection reasons.
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
    Resumes when marketer sends approval/edit/rejection payload with structured rejection reason.
    """
    thread_id = state.get("thread_id", "")
    community_id = state.get("community_id") or state.get("subreddit", "r/general")
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
        "community_id": community_id,
        "subreddit": state.get("subreddit", community_id),
        "title": title,
        "body": state.get("body", ""),
        "author": state.get("author", "[deleted]"),
        "permalink": state.get("permalink", ""),
        "discovery_score": state.get("discovery_score", 0.0),
        "discovery_passed": state.get("discovery_passed", True),
        "extracted_problem": state.get("extracted_problem", ""),
        "pain_point": state.get("pain_point", ""),
        "conversation_context": state.get("conversation_context", ""),
        "community_context": state.get("community_context", ""),
        "user_goal": state.get("user_goal", ""),
        "user_intent": state.get("user_intent", "general_discussion"),
        "sentiment": state.get("sentiment", "neutral"),
        "entities": state.get("entities", []),
        "brand_mentioned": state.get("brand_mentioned", False),
        "competitor_mentioned": state.get("competitor_mentioned", False),
        "mentioned_brands": state.get("mentioned_brands", []),
        "mentioned_competitors": state.get("mentioned_competitors", []),
        "evidence_quote": evidence_quote,
        "evidence": state.get("evidence", [evidence_quote] if evidence_quote else []),
        "analyst_confidence": state.get("analyst_confidence", 0.85),
        "relevance_score": state.get("relevance_score", 0),
        "intent_strength_score": state.get("intent_strength_score", 0),
        "community_fit_score": state.get("community_fit_score", 0),
        "credibility_score": state.get("credibility_score", 0),
        "engagement_risk_score": state.get("engagement_risk_score", 0),
        "opportunity_score": opportunity_score,
        "strategist_confidence": state.get("strategist_confidence", 0.85),
        "engagement_decision": state.get("engagement_decision", "engage"),
        "strategic_reasoning": state.get("strategic_reasoning", ""),
        "sensitive_topic": state.get("sensitive_topic", False),
        "sensitive_topic_reason": state.get("sensitive_topic_reason"),
        "proposed_draft": proposed_draft,
        "draft_iteration": state.get("draft_iteration", 0),
        "critic_passed": critic_passed,
        "violation_category": violation_category,
        "critic_feedback": state.get("critic_feedback"),
    }

    # Halts graph execution, saves state to checkpointer, yields payload for UI
    decision = interrupt(full_payload)

    # Validate resumed payload
    human_status = decision.get("action", "approved").lower() if isinstance(decision, dict) else "approved"
    final_text = decision.get("final_response_text", proposed_draft) if isinstance(decision, dict) else proposed_draft
    rejection_reason = decision.get("rejection_reason") if isinstance(decision, dict) else None

    logger.info(
        f"[HumanReviewNode] Resumed thread {thread_id} with decision: {human_status}"
        + (f" (Reason: {rejection_reason})" if rejection_reason else "")
    )

    # Persist final decision in SQLite
    await record_human_triage(
        thread_id=thread_id,
        human_status=human_status,
        final_response_text=final_text,
        rejection_reason=rejection_reason,
    )

    return {
        "human_status": human_status,
        "final_response_text": final_text,
        "rejection_reason": rejection_reason,
    }
