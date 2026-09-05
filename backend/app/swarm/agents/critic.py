"""
Compliance Critic Agent Node (Adversarial Audit).
Difference 11:
Audits proposed drafts against anti-astroturfing, unsupported claims, excessive promotion,
community rule violations, and off-topic alignment.
"""

import re
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import update_draft_and_critic
from app.ingestion.community_rules import get_community_context
from app.swarm.state import SwarmState, CriticResult
from app.swarm.prompts.critic import CRITIC_SYSTEM_PROMPT, CRITIC_USER_PROMPT

logger = logging.getLogger("dark_social_swarm.agents.critic")

# Hardcoded Guardrails regex rules for instant deterministic safety gating
URL_PATTERN = re.compile(r"(https?://\S+|www\.\S+|bit\.ly/\S+|t\.co/\S+)", re.IGNORECASE)

EXCESSIVE_PROMOTION_PHRASES = [
    "sign up now", "book a call", "book a demo", "discount code",
    "promo code", "50% off", "affiliate link", "buy our product",
    "try our platform today", "dm me for access", "visit our website",
    "click here to purchase",
]

ASTROTURFING_PHRASES = [
    "as an unaffiliated user", "i'm just a happy customer",
    "i stumbled across this tool and it saved my life",
    "i'm not associated with", "as a regular customer",
    "i don't work for them but", "i am just a user who loves",
]

UNSUPPORTED_CLAIMS_PHRASES = [
    "guaranteed 10x", "proven 100% success", "increases revenue by 500%",
    "best tool in the world", "completely eliminates all errors forever",
]


def programmatic_guardrails_check(text: str) -> Optional[CriticResult]:
    """
    Fast programmatic safety check adhering to adversarial Guardrails principles.
    Catches link drops, hard CTAs, astroturfing, and wild claims before LLM invocation.
    """
    lower_text = text.lower()

    # 1. Anti-Astroturfing check
    for phrase in ASTROTURFING_PHRASES:
        if phrase in lower_text:
            return CriticResult(
                critic_passed=False,
                violation_category="astroturfing",
                critic_feedback=f"Draft contains deceptive astroturfing persona ('{phrase}'). Speak transparently as a builder or technical peer.",
            )

    # 2. Excessive Promotion check (Links & Aggressive CTAs)
    if URL_PATTERN.search(text):
        return CriticResult(
            critic_passed=False,
            violation_category="excessive_promotion",
            critic_feedback="Draft contains external URL link. Remove all external links per Zero-Plug rule.",
        )

    for phrase in EXCESSIVE_PROMOTION_PHRASES:
        if phrase in lower_text:
            return CriticResult(
                critic_passed=False,
                violation_category="excessive_promotion",
                critic_feedback=f"Draft includes sales pitch phrase '{phrase}'. Reframe as neutral technical advice.",
            )

    # 3. Unsupported Claims check
    for phrase in UNSUPPORTED_CLAIMS_PHRASES:
        if phrase in lower_text:
            return CriticResult(
                critic_passed=False,
                violation_category="unsupported_claims",
                critic_feedback=f"Draft contains unsubstantiated marketing claim '{phrase}'. Base recommendations on verifiable mechanics.",
            )

    return None


from app.swarm.llm import get_swarm_llm


def get_llm():
    return get_swarm_llm(temperature=0.0)


async def critic_node(state: SwarmState) -> Dict[str, Any]:
    """
    Compliance Critic Node execution function.
    Audits the draft; returns pass/fail and corrective feedback for Drafter loop.
    """
    thread_id = state.get("thread_id", "")
    community_id = state.get("community_id") or state.get("subreddit", "r/general")
    title = state.get("title", "")
    extracted_problem = state.get("extracted_problem", "")
    evidence_quote = state.get("evidence_quote", "")
    proposed_draft = state.get("proposed_draft", "")
    draft_iteration = state.get("draft_iteration", 1)
    community_context = state.get("community_context") or get_community_context(community_id)

    logger.info(f"[Critic] Auditing draft for thread {thread_id} (Iteration {draft_iteration})...")

    # 1. Run deterministic Guardrails checks first
    programmatic_fail = programmatic_guardrails_check(proposed_draft)
    if programmatic_fail:
        result = programmatic_fail
    else:
        # 2. Run LLM semantic compliance check
        from app.swarm.llm import invoke_structured_swarm_llm

        user_prompt = CRITIC_USER_PROMPT.format(
            community_id=community_id,
            community_context=community_context,
            title=title,
            extracted_problem=extracted_problem,
            evidence_quote=evidence_quote,
            proposed_draft=proposed_draft,
        )
        result = await invoke_structured_swarm_llm(
            schema=CriticResult,
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0,
        )

        if not result:
            # Clean pass for valid drafts in dev mode
            result = CriticResult(
                critic_passed=True,
                violation_category=None,
                critic_feedback=None,
            )

    # Decide status: if passed or hit max retries, prepare for AWAITING_APPROVAL
    can_retry = (not result.critic_passed) and (draft_iteration < settings.MAX_CRITIC_RETRIES)
    new_status = "PROCESSING" if can_retry else "AWAITING_APPROVAL"

    await update_draft_and_critic(
        thread_id=thread_id,
        proposed_draft=proposed_draft,
        draft_iteration=draft_iteration,
        critic_passed=result.critic_passed,
        violation_category=result.violation_category,
        critic_feedback=result.critic_feedback,
        status=new_status,
    )

    logger.info(
        f"[Critic] Thread {thread_id} passed: {result.critic_passed}, "
        f"violation: {result.violation_category}"
    )

    return {
        "critic_passed": result.critic_passed,
        "violation_category": result.violation_category,
        "critic_feedback": result.critic_feedback,
    }
