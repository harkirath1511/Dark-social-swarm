"""
Strategist Agent Node (Evaluation & Opportunity Scoring).
Calculates Opportunity Score (0-100) and produces engagement verdict.
"""

import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import update_strategist_decision
from app.swarm.state import SwarmState, StrategistResult
from app.swarm.prompts.strategist import STRATEGIST_SYSTEM_PROMPT, STRATEGIST_USER_PROMPT

logger = logging.getLogger("dark_social_swarm.agents.strategist")


def get_llm():
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
        return ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1,
        )
    return None


async def strategist_node(state: SwarmState) -> Dict[str, Any]:
    """
    Strategist Node execution function.
    Evaluates fit, brand risk, and commercial urgency to produce Opportunity Score.
    """
    thread_id = state.get("thread_id", "")
    subreddit = state.get("subreddit", "")
    title = state.get("title", "")
    extracted_problem = state.get("extracted_problem", "")
    user_intent = state.get("user_intent", "medium")
    evidence_quote = state.get("evidence_quote", "")

    logger.info(f"[Strategist] Evaluating opportunity for thread {thread_id}...")

    llm = get_llm()
    if llm:
        structured_llm = llm.with_structured_output(StrategistResult)
        messages = [
            SystemMessage(content=STRATEGIST_SYSTEM_PROMPT),
            HumanMessage(content=STRATEGIST_USER_PROMPT.format(
                subreddit=subreddit,
                title=title,
                extracted_problem=extracted_problem,
                user_intent=user_intent,
                evidence_quote=evidence_quote,
            )),
        ]
        result: StrategistResult = await structured_llm.ainvoke(messages)
    else:
        # Heuristic scoring fallback for dev/test without API keys
        is_spam = any(w in (title + extracted_problem).lower() for w in ["discount", "50% off", "promo code", "backlink package"])
        if is_spam:
            score = 15
            decision = "do_not_engage"
            reasoning = "Identified as promotional submission or low intent."
        elif user_intent == "high":
            score = 85
            decision = "engage"
            reasoning = "High commercial intent and direct alignment with workflow bottlenecks."
        else:
            score = 65
            decision = "maybe_engage"
            reasoning = "Moderate discussion interest with relevant community context."

        result = StrategistResult(
            opportunity_score=score,
            engagement_decision=decision,
            strategic_reasoning=reasoning,
        )

    # If score < threshold, route to DISCARDED
    new_status = "DISCARDED" if (result.opportunity_score < settings.OPPORTUNITY_SCORE_THRESHOLD or result.engagement_decision == "do_not_engage") else "PROCESSING"

    await update_strategist_decision(
        thread_id=thread_id,
        opportunity_score=result.opportunity_score,
        engagement_decision=result.engagement_decision,
        strategic_reasoning=result.strategic_reasoning,
        status=new_status,
    )

    logger.info(f"[Strategist] Thread {thread_id} Score: {result.opportunity_score}, Decision: {result.engagement_decision}")
    return {
        "opportunity_score": result.opportunity_score,
        "engagement_decision": result.engagement_decision,
        "strategic_reasoning": result.strategic_reasoning,
    }
