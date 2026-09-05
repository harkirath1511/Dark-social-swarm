"""
LangGraph StateGraph Engine Assembly & Conditional Routing.
Differences 10, 12:
- 5-stage Multi-Agent Swarm with Sensitive Topic Gate & Bounded Critic Retry Loop.
- Drops discussions with Opportunity Score < 40 or 'do_not_engage'.
- Evaluates medical, legal, and crisis topics: bypasses automated drafting and routes directly to human_review.
- Audits drafts with Compliance Critic; loops back to drafter on failure up to MAX_CRITIC_RETRIES (2 iterations).
"""

import re
import logging
from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.core.database import update_sensitive_topic
from app.swarm.state import SwarmState
from app.swarm.agents.analyst import analyst_node
from app.swarm.agents.strategist import strategist_node
from app.swarm.agents.drafter import drafter_node
from app.swarm.agents.critic import critic_node
from app.swarm.agents.human_review import human_review_node

logger = logging.getLogger("dark_social_swarm.graph")

SENSITIVE_PATTERNS = [
    # Medical & Mental Health Crisis
    r"\b(medical|diagnosis|prescription|doctor|hospital|cancer|illness|disease|surgery)\b",
    r"\b(suicid(e|al)|self-harm|depression|mental\s+breakdown|emergency\s+room)\b",
    # Legal Crisis & Litigation
    r"\b(lawsuit|suing|sued|subpoena|litigation|attorney|lawyer|court\s+case|cease\s+and\s+desist|arrested|criminal\s+charges)\b",
    r"\b(legal\s+crisis|patent\s+infringement|copyright\s+strike|dmca\s+threat)\b",
    # Toxic & Harassment
    r"\b(harassment|doxx(ed|ing)|death\s+threat|stalking)\b",
]
COMPILED_SENSITIVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]


async def sensitive_topic_gate_node(state: SwarmState) -> Dict[str, Any]:
    """
    Difference 10: Sensitive Topic Gate.
    Scans discussion text for medical, legal, crisis, or toxic subjects.
    If sensitive, sets sensitive_topic = True so automated drafting is bypassed.
    """
    thread_id = state.get("thread_id", "")
    title = state.get("title", "")
    body = state.get("body", "")
    extracted_problem = state.get("extracted_problem", "")
    full_text = f"{title} {body} {extracted_problem}".lower()

    matched_reasons = []
    for pattern in COMPILED_SENSITIVE_PATTERNS:
        matches = pattern.findall(full_text)
        if matches:
            matched_reasons.extend([m if isinstance(m, str) else m[0] for m in matches])

    is_sensitive = len(matched_reasons) > 0
    reason = (
        f"Sensitive topic detected: contains sensitive keywords ({', '.join(set(matched_reasons))}). "
        f"Bypassing automated drafting for safety."
        if is_sensitive
        else None
    )

    if is_sensitive:
        logger.warning(f"[SensitiveGate] Thread {thread_id} flagged as sensitive! Reason: {reason}")
        await update_sensitive_topic(thread_id, sensitive_topic=True, sensitive_topic_reason=reason)

    return {
        "sensitive_topic": is_sensitive,
        "sensitive_topic_reason": reason,
    }


# -------------------------------------------------------------
# Conditional Routing Functions
# -------------------------------------------------------------

def route_after_strategist(state: SwarmState) -> Literal["sensitive_gate", "__end__"]:
    """
    Evaluates Strategist verdict and Opportunity Score.
    Score < 40 or 'do_not_engage' drops execution immediately.
    Otherwise passes to the Sensitive Topic Gate.
    """
    score = state.get("opportunity_score", 0) or 0
    decision = state.get("engagement_decision", "do_not_engage")

    if score < settings.OPPORTUNITY_SCORE_THRESHOLD or decision == "do_not_engage":
        logger.info(f"Dropping post (Score: {score}, Decision: {decision}). Routing to END.")
        return END

    logger.info(f"Opportunity qualified (Score: {score}, Decision: {decision}). Routing to Sensitive Gate.")
    return "sensitive_gate"


def route_after_sensitive_gate(state: SwarmState) -> Literal["human_review", "drafter"]:
    """
    Difference 10:
    If conversation touches medical, legal, crisis, or toxic subjects,
    bypass Drafter and route straight to Human Review for manual triage.
    """
    if state.get("sensitive_topic", False):
        logger.info("Sensitive topic gate triggered. Bypassing Drafter -> routing to Human Review.")
        return "human_review"

    return "drafter"


def route_after_critic(state: SwarmState) -> Literal["drafter", "human_review"]:
    """
    Difference 12: Bounded Critic Retry Loop.
    If failed and retries remain (< 2 iterations), loops back to Drafter with feedback.
    Otherwise, proceeds to Human Review node (flags attached if retries exhausted).
    """
    passed = state.get("critic_passed", False)
    iteration = state.get("draft_iteration", 0)

    if not passed and iteration < settings.MAX_CRITIC_RETRIES:
        logger.info(
            f"Critic audit failed (Iteration {iteration} < {settings.MAX_CRITIC_RETRIES}). "
            f"Routing back to Drafter with feedback."
        )
        return "drafter"

    logger.info("Draft approved by Critic (or reached max retries). Routing to Human Review Node.")
    return "human_review"


# -------------------------------------------------------------
# StateGraph Builder & Compiler
# -------------------------------------------------------------

def build_swarm_graph():
    """Constructs the master StateGraph with Sensitive Topic Gate & Bounded Retry Loop."""
    builder = StateGraph(SwarmState)

    # Specialized Nodes
    builder.add_node("analyst", analyst_node)
    builder.add_node("strategist", strategist_node)
    builder.add_node("sensitive_gate", sensitive_topic_gate_node)
    builder.add_node("drafter", drafter_node)
    builder.add_node("critic", critic_node)
    builder.add_node("human_review", human_review_node)

    # Flow Edges
    builder.add_edge(START, "analyst")
    builder.add_edge("analyst", "strategist")

    # Conditional Branch 1: Strategist Filter (Drop vs Sensitive Gate)
    builder.add_conditional_edges(
        "strategist",
        route_after_strategist,
        {
            "sensitive_gate": "sensitive_gate",
            END: END,
        }
    )

    # Conditional Branch 2: Sensitive Gate (Bypass Draft to Human Review vs Drafter)
    builder.add_conditional_edges(
        "sensitive_gate",
        route_after_sensitive_gate,
        {
            "human_review": "human_review",
            "drafter": "drafter",
        }
    )

    # Drafter -> Critic
    builder.add_edge("drafter", "critic")

    # Conditional Branch 3: Critic Audit Loop (Re-draft vs Human Review)
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "drafter": "drafter",
            "human_review": "human_review",
        }
    )

    # Human Review -> END
    builder.add_edge("human_review", END)

    return builder


def compile_swarm_graph(checkpointer=None):
    """
    Compiles the StateGraph with a checkpointer for durable state & interrupt() resumption.
    """
    builder = build_swarm_graph()
    active_checkpointer = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=active_checkpointer)


# Default compiled graph instance
default_checkpointer = MemorySaver()
swarm_app = compile_swarm_graph(checkpointer=default_checkpointer)
