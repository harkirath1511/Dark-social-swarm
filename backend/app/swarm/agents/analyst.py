"""
Analyst Agent Node (Scout Persona).
Differences 2, 3, 5, 7, 9:
Extracts underlying problem, pain point, conversation context, community context,
user goal, classified intent, sentiment, entities, brand & competitor flags,
multi-sentence verbatim evidence, and analyst confidence.
"""

import re
import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import update_analyst_signals
from app.ingestion.discovery import evaluate_candidate_discovery
from app.ingestion.community_rules import get_community_context
from app.swarm.state import SwarmState, AnalystResult
from app.swarm.prompts.analyst import ANALYST_SYSTEM_PROMPT, ANALYST_USER_PROMPT

logger = logging.getLogger("dark_social_swarm.agents.analyst")

# Known competitor tools in the SaaS / productivity / automation space for deterministic heuristic recognition
KNOWN_COMPETITORS = [
    "hubspot", "salesforce", "zapier", "make.com", "notion", "airtable",
    "descript", "opusclip", "capcut", "hootsuite", "buffer", "sprout social",
    "gong", "apollo", "outreach", "pipedrive", "intercom", "drift"
]
# Our brand identifier (to check if brand was mentioned)
OUR_BRANDS = ["dark social swarm", "darksocialswarm"]


from app.swarm.llm import get_swarm_llm


def get_llm():
    return get_swarm_llm(temperature=0.1)


def extract_heuristic_evidence(title: str, body: str) -> List[str]:
    """Extract 1 to 3 observable verbatim sentence quotes from title and body."""
    candidates = []
    full_text = f"{title}. {body}".strip()
    # Split text by sentence terminators
    raw_sentences = [s.strip() for s in re.split(r"[.!?\n]+", full_text) if len(s.strip()) > 15]

    for sentence in raw_sentences:
        # Prioritize sentences with pain points or question marks
        lower = sentence.lower()
        if any(w in lower for w in ["which", "tried", "none", "struggl", "hate", "killing", "recommend", "how do", "can't", "problem", "broken", "actually works", "wasting"]):
            candidates.append(sentence)
        elif len(candidates) < 2 and len(sentence) > 20:
            candidates.append(sentence)

    if not candidates:
        candidates = [title]

    # Return up to 3 unique verbatim quotes
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)
    return unique_candidates[:3]


async def analyst_node(state: SwarmState) -> Dict[str, Any]:
    """
    Analyst Node execution function.
    Parses thread context, identifies core problem, assesses intent, entities, sentiment,
    and extracts multi-sentence verbatim evidence quotes.
    """
    thread_id = state.get("thread_id", "")
    community_id = state.get("community_id") or state.get("subreddit", "r/general")
    title = state.get("title", "")
    body = state.get("body", "")
    author = state.get("author", "")

    # 1. Obtain community context norms
    community_context = get_community_context(community_id)

    # 2. Run Candidate Discovery evaluation if not already evaluated
    discovery_passed = state.get("discovery_passed")
    discovery_score = state.get("discovery_score")
    if discovery_score is None or discovery_score == 0.0:
        discovery_passed, discovery_score = evaluate_candidate_discovery(f"{title}\n{body}")

    logger.info(f"[Analyst] Analyzing thread {thread_id} in {community_id} (Discovery Score: {discovery_score})...")

    from app.swarm.llm import invoke_structured_swarm_llm

    user_prompt = ANALYST_USER_PROMPT.format(
        community_id=community_id,
        community_context=community_context,
        author=author,
        title=title,
        body=body or "(No self-text, title only)"
    )
    result = await invoke_structured_swarm_llm(
        schema=AnalystResult,
        system_prompt=ANALYST_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.1,
    )

    if not result:
        # Deterministic heuristic extraction for dev/test mode
        combined_text = f"{title} {body}".strip()
        lower_text = combined_text.lower()

        # Evidence quotes
        evidence_list = extract_heuristic_evidence(title, body)
        primary_quote = evidence_list[0] if evidence_list else title

        # Brand & competitor detection
        brand_matched = [b for b in OUR_BRANDS if b in lower_text]
        competitors_matched = [c for c in KNOWN_COMPETITORS if c in lower_text]

        # Intent classification
        if any(w in lower_text for w in ["which one", "recommend", "looking for", "what tool", "which video editing tool", "which crm"]):
            intent = "recommendation_seeking"
        elif any(w in lower_text for w in ["alternative", "switch from", "replace", "hate using", "tired of"]):
            intent = "alternative_seeking"
        elif any(w in lower_text for w in ["mid-sentence", "bug", "broken", "does not work", "error", "failing"]):
            intent = "troubleshooting"
        elif any(w in lower_text for w in ["manual", "killing our", "wasting hours", "friction", "bottleneck"]):
            intent = "workflow_friction"
        elif any(w in lower_text for w in ["how do you", "what is the best practice", "guide", "learn"]):
            intent = "educational"
        else:
            intent = "general_discussion"

        # Sentiment classification
        if any(w in lower_text for w in ["hate", "killing", "tired", "frustrat", "broken", "sucks", "nightmare"]):
            sentiment = "frustrated"
        elif any(w in lower_text for w in ["actually works?", "none of them", "doubt", "skeptical"]):
            sentiment = "skeptical"
        elif any(w in lower_text for w in ["curious", "wondering", "anyone know"]):
            sentiment = "curious"
        else:
            sentiment = "neutral"

        # Entity extraction
        domain_entities = []
        for kw in ["crm", "video editing", "podcasts", "slack", "hubspot", "clips", "ai sdrs", "lead tracking", "social listening"]:
            if kw in lower_text:
                domain_entities.append(kw.upper() if len(kw) <= 4 else kw.title())

        # Pain point & problem
        core_problem = f"User is asking: {title}"
        pain_point = "Friction caused by existing workflows or tools failing to meet operational expectations."
        user_goal = "Find a reliable tool or methodology that solves their specific bottleneck."

        result = AnalystResult(
            extracted_problem=core_problem,
            pain_point=pain_point,
            conversation_context=f"Discussion initiated by {author} in {community_id}. Context involves {', '.join(domain_entities) if domain_entities else 'operational workflow'}.",
            community_context=community_context,
            user_goal=user_goal,
            user_intent=intent,
            sentiment=sentiment,
            entities=domain_entities,
            brand_mentioned=len(brand_matched) > 0,
            competitor_mentioned=len(competitors_matched) > 0,
            mentioned_brands=brand_matched,
            mentioned_competitors=competitors_matched,
            evidence_quote=primary_quote,
            evidence=evidence_list,
            analyst_confidence=0.90 if discovery_score > 0.6 else 0.75,
        )

    # Persist findings to database
    await update_analyst_signals(
        thread_id=thread_id,
        extracted_problem=result.extracted_problem,
        user_intent=result.user_intent,
        evidence_quote=result.evidence_quote,
        pain_point=result.pain_point,
        conversation_context=result.conversation_context,
        community_context=community_context,
        user_goal=result.user_goal,
        sentiment=result.sentiment,
        entities=result.entities,
        brand_mentioned=result.brand_mentioned,
        competitor_mentioned=result.competitor_mentioned,
        mentioned_brands=result.mentioned_brands,
        mentioned_competitors=result.mentioned_competitors,
        evidence=result.evidence,
        analyst_confidence=result.analyst_confidence,
    )

    logger.info(
        f"[Analyst] Thread {thread_id} intent: {result.user_intent}, "
        f"brand_mentioned: {result.brand_mentioned}, "
        f"quotes: {len(result.evidence)}"
    )

    return {
        "community_id": community_id,
        "community_context": community_context,
        "discovery_score": discovery_score,
        "discovery_passed": discovery_passed,
        "extracted_problem": result.extracted_problem,
        "pain_point": result.pain_point,
        "conversation_context": result.conversation_context,
        "user_goal": result.user_goal,
        "user_intent": result.user_intent,
        "sentiment": result.sentiment,
        "entities": result.entities,
        "brand_mentioned": result.brand_mentioned,
        "competitor_mentioned": result.competitor_mentioned,
        "mentioned_brands": result.mentioned_brands,
        "mentioned_competitors": result.mentioned_competitors,
        "evidence_quote": result.evidence_quote,
        "evidence": result.evidence,
        "analyst_confidence": result.analyst_confidence,
    }
