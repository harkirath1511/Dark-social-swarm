"""
Strategist Agent Node (Evaluation & 6D Scoring).
Differences 4, 6, 7, 8, 16, 18:
Calculates relevance, intent strength, community fit, credibility, and engagement risk.
Computes composite Opportunity Score, evaluates engagement decision,
assigns confidence, and provides explainable strategic reasoning.
"""

import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import update_strategist_decision
from app.ingestion.community_rules import get_community_rules, get_community_context
from app.swarm.state import SwarmState, StrategistResult
from app.swarm.prompts.strategist import STRATEGIST_SYSTEM_PROMPT, STRATEGIST_USER_PROMPT

logger = logging.getLogger("dark_social_swarm.agents.strategist")


from app.swarm.llm import get_swarm_llm


def get_llm():
    return get_swarm_llm(temperature=0.1, reasoning=True)


def calculate_composite_score(
    relevance: int,
    intent: int,
    community_fit: int,
    risk: int,
) -> int:
    """
    Computes composite Opportunity Score:
    User Value (40%) + Intent (30%) + Community Fit (20%) - Risk (10%)
    """
    weighted = (0.40 * relevance) + (0.30 * intent) + (0.20 * community_fit) - (0.10 * risk)
    return max(0, min(100, int(round(weighted))))


async def strategist_node(state: SwarmState) -> Dict[str, Any]:
    """
    Strategist Node execution function.
    Performs 6-dimensional evaluation and decides whether to engage, maybe engage, or drop.
    """
    thread_id = state.get("thread_id", "")
    community_id = state.get("community_id") or state.get("subreddit", "r/general")
    title = state.get("title", "")
    body = state.get("body", "")
    author = state.get("author", "")
    extracted_problem = state.get("extracted_problem", "")
    pain_point = state.get("pain_point", "")
    user_goal = state.get("user_goal", "")
    user_intent = state.get("user_intent", "general_discussion")
    sentiment = state.get("sentiment", "neutral")
    entities = state.get("entities", [])
    brand_mentioned = state.get("brand_mentioned", False)
    competitor_mentioned = state.get("competitor_mentioned", False)
    evidence_quote = state.get("evidence_quote", "")
    community_context = state.get("community_context") or get_community_context(community_id)

    logger.info(f"[Strategist] Evaluating opportunity for thread {thread_id} in {community_id}...")

    from app.swarm.llm import invoke_structured_swarm_llm

    user_prompt = STRATEGIST_USER_PROMPT.format(
        community_id=community_id,
        community_context=community_context,
        author=author,
        title=title,
        extracted_problem=extracted_problem,
        pain_point=pain_point,
        user_goal=user_goal,
        user_intent=user_intent,
        sentiment=sentiment,
        entities=entities,
        brand_mentioned=brand_mentioned,
        competitor_mentioned=competitor_mentioned,
        evidence_quote=evidence_quote,
    )
    result = await invoke_structured_swarm_llm(
        schema=StrategistResult,
        system_prompt=STRATEGIST_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.1,
        reasoning=True,
    )

    if not result:
        # Deterministic 6D heuristic evaluation
        rules = get_community_rules(community_id)
        combined_text = f"{title} {body}".lower()

        # Check for failed candidate discovery or promotional spam signals
        discovery_passed = state.get("discovery_passed", True)
        is_promo_spam = any(w in combined_text for w in [
            "discount code", "promo code", "50% off", "cheap seo", "buy our", "sign up now", "affiliate link"
        ])

        if not discovery_passed or is_promo_spam:
            intent_strength = 10
            relevance = 10
            community_fit = 10
            engagement_risk = 90
            opportunity_score = 10
            decision = "do_not_engage"
            reasoning = "Dropped: Post exhibits promotional spam patterns or failed problem discovery pre-filter."
            result = StrategistResult(
                relevance_score=relevance,
                intent_strength_score=intent_strength,
                community_fit_score=community_fit,
                credibility_score=20,
                engagement_risk_score=engagement_risk,
                opportunity_score=opportunity_score,
                strategist_confidence=0.95,
                engagement_decision=decision,
                strategic_reasoning=reasoning,
            )
        else:
            # 1. Intent Strength Score
            if user_intent in ("recommendation_seeking", "alternative_seeking"):
                intent_strength = 92
            elif user_intent in ("troubleshooting", "workflow_friction"):
                intent_strength = 82
            elif user_intent == "educational":
                intent_strength = 60
            else:
                intent_strength = 35

            # Boost if user explicitly asked "which one actually works" or similar
            if "actually works" in combined_text or "which one" in combined_text:
                intent_strength = max(intent_strength, 95)

        # 2. Relevance Score (Domain fit: video editing, automation, CRM, SaaS productivity)
        is_core_domain = any(kw in combined_text for kw in [
            "video", "clip", "editing", "crm", "hubspot", "podcast", "audio", "sales", "ai sdr", "social listening", "workflow"
        ])
        relevance = 95 if is_core_domain else 55

        # 3. Community Fit Score
        fit_mod = rules.get("fit_modifier", 0.9)
        community_fit = int(round(90 * fit_mod))

        # 4. Credibility Score
        credibility = 90 if len(evidence_quote) > 15 else 60

        # 5. Engagement Risk Score (higher = riskier)
        risk_mod = rules.get("risk_modifier", 1.0)
        base_risk = 12
        if rules.get("scrutiny_level") == "extreme":
            base_risk += 35
        engagement_risk = int(round(base_risk * risk_mod))

        # 6. Opportunity Score (Composite)
        opportunity_score = calculate_composite_score(
            relevance=relevance,
            intent=intent_strength,
            community_fit=community_fit,
            risk=engagement_risk,
        )

        # Engagement decision
        if opportunity_score >= 70 and engagement_risk <= 50:
            decision = "engage"
        elif opportunity_score >= 40 and engagement_risk <= 75:
            decision = "maybe_engage"
        else:
            decision = "do_not_engage"

        # Strategic reasoning
        reasoning = (
            f"Why this user: User is actively seeking solutions for '{title[:60]}...' with strong {user_intent} intent. "
            f"Why this community: {community_id} moderation parameters ({rules.get('scrutiny_level')} scrutiny) allow value-first advice. "
            f"Why now: Timely problem-solving opportunity with observable pain point evidence."
        )

        result = StrategistResult(
            relevance_score=relevance,
            intent_strength_score=intent_strength,
            community_fit_score=community_fit,
            credibility_score=credibility,
            engagement_risk_score=engagement_risk,
            opportunity_score=opportunity_score,
            strategist_confidence=0.88,
            engagement_decision=decision,
            strategic_reasoning=reasoning,
        )

    # Decide next lifecycle status
    next_status = "PROCESSING" if result.engagement_decision != "do_not_engage" else "DISCARDED"

    # Persist to database
    await update_strategist_decision(
        thread_id=thread_id,
        opportunity_score=result.opportunity_score,
        engagement_decision=result.engagement_decision,
        strategic_reasoning=result.strategic_reasoning,
        status=next_status,
        relevance_score=result.relevance_score,
        intent_strength_score=result.intent_strength_score,
        community_fit_score=result.community_fit_score,
        credibility_score=result.credibility_score,
        engagement_risk_score=result.engagement_risk_score,
        strategist_confidence=result.strategist_confidence,
    )

    logger.info(
        f"[Strategist] Thread {thread_id} Score: {result.opportunity_score} "
        f"(Rel: {result.relevance_score}, Intent: {result.intent_strength_score}, Fit: {result.community_fit_score}, Risk: {result.engagement_risk_score}), "
        f"Decision: {result.engagement_decision}"
    )

    return {
        "relevance_score": result.relevance_score,
        "intent_strength_score": result.intent_strength_score,
        "community_fit_score": result.community_fit_score,
        "credibility_score": result.credibility_score,
        "engagement_risk_score": result.engagement_risk_score,
        "opportunity_score": result.opportunity_score,
        "strategist_confidence": result.strategist_confidence,
        "engagement_decision": result.engagement_decision,
        "strategic_reasoning": result.strategic_reasoning,
    }
