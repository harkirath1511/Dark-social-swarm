"""
LangGraph StateGraph Engine Assembly & Conditional Routing.
Adapted from KirtiJha/langgraph-interrupt-workflow-template:
- Defines the 5-stage Multi-Agent Swarm
- Conditional routing based on Opportunity Score and Critic Pass/Fail
- Configures durable state checkpointer and native interrupt()
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.swarm.state import SwarmState
from app.swarm.agents.analyst import analyst_node
from app.swarm.agents.strategist import strategist_node
from app.swarm.agents.drafter import drafter_node
from app.swarm.agents.critic import critic_node
from app.swarm.agents.human_review import human_review_node

logger = logging.getLogger("dark_social_swarm.graph")


# -------------------------------------------------------------
# Conditional Routing Functions
# -------------------------------------------------------------

def route_after_strategist(state: SwarmState) -> Literal["drafter", "__end__"]:
    """
    Evaluates Strategist verdict and Opportunity Score.
    Score < 40 or 'do_not_engage' drops execution immediately.
    """
    score = state.get("opportunity_score", 0) or 0
    decision = state.get("engagement_decision", "do_not_engage")

    if score < settings.OPPORTUNITY_SCORE_THRESHOLD or decision == "do_not_engage":
        logger.info(f"Dropping post (Score: {score}, Decision: {decision}). Routing to END.")
        return END

    logger.info(f"Opportunity qualified (Score: {score}, Decision: {decision}). Routing to Drafter.")
    return "drafter"


def route_after_critic(state: SwarmState) -> Literal["drafter", "human_review"]:
    """
    Evaluates Compliance Critic verdict.
    If failed and retries remain (< 2), loops back to Drafter with feedback.
    Otherwise, proceeds to Human Review node (flags attached if retries exhausted).
    """
    passed = state.get("critic_passed", False)
    iteration = state.get("draft_iteration", 0)

    if not passed and iteration < settings.MAX_CRITIC_RETRIES:
        logger.info(f"Critic audit failed (Iteration {iteration} < {settings.MAX_CRITIC_RETRIES}). Routing back to Drafter.")
        return "drafter"

    logger.info("Draft approved by Critic (or reached max retries). Routing to Human Review Node.")
    return "human_review"


# -------------------------------------------------------------
# StateGraph Builder & Compiler
# -------------------------------------------------------------

def build_swarm_graph():
    """Constructs the master StateGraph without compiling."""
    builder = StateGraph(SwarmState)

    # Add 5 specialized nodes
    builder.add_node("analyst", analyst_node)
    builder.add_node("strategist", strategist_node)
    builder.add_node("drafter", drafter_node)
    builder.add_node("critic", critic_node)
    builder.add_node("human_review", human_review_node)

    # Add flow edges
    builder.add_edge(START, "analyst")
    builder.add_edge("analyst", "strategist")

    # Conditional branch 1: Strategist filter (Drop vs Engage)
    builder.add_conditional_edges(
        "strategist",
        route_after_strategist,
        {
            "drafter": "drafter",
            END: END,
        }
    )

    # Drafting -> Critic
    builder.add_edge("drafter", "critic")

    # Conditional branch 2: Critic audit loop (Re-draft vs Human Review)
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
