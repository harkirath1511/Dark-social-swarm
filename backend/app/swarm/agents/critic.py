"""
Compliance Critic Agent Node (Guardrails validation).
Audits proposed drafts against factual grounding, anti-astroturfing, and anti-spam guidelines.
"""

import re
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import update_draft_and_critic
from app.swarm.state import SwarmState, CriticResult
from app.swarm.prompts.critic import CRITIC_SYSTEM_PROMPT, CRITIC_USER_PROMPT

logger = logging.getLogger("dark_social_swarm.agents.critic")

# Hardcoded Guardrails regex rules for instant deterministic safety gating
URL_PATTERN = re.compile(r"(https?://\S+|www\.\S+|bit\.ly/\S+|t\.co/\S+)", re.IGNORECASE)
AGGRESSIVE_PHRASES = [
    "sign up now", "book a call", "book a demo", "discount code",
    "promo code", "50% off", "affiliate link", "buy our product",
    "try our platform today", "dm me for access",
]
ASTROTURF_PHRASES = [
    "as an unaffiliated user", "i'm just a happy customer",
    "i stumbled across this tool and it saved my life",
]


def programmatic_guardrails_check(text: str) -> Optional[CriticResult]:
    """
    Fast programmatic safety check adhering to Guardrails principles.
    Catches link drops, hard CTAs, and astroturfing before LLM invocation.
    """
    # 1. Zero-plug check (no URLs)
    if URL_PATTERN.search(text):
        return CriticResult(
            critic_passed=False,
            violation_category="unsolicited_promotion",
            critic_feedback="Draft contains external URL link. Remove all product links per Zero-Plug rule.",
        )

    # 2. Aggressive sales CTA check
    lower_text = text.lower()
    for phrase in AGGRESSIVE_PHRASES:
        if phrase in lower_text:
            return CriticResult(
                critic_passed=False,
                violation_category="aggressive_cta",
                critic_feedback=f"Draft includes sales pitch phrase '{phrase}'. Reframe as neutral technical advice.",
            )

    # 3. Astroturfing check
    for phrase in ASTROTURF_PHRASES:
        if phrase in lower_text:
            return CriticResult(
                critic_passed=False,
                violation_category="astroturfing",
                critic_feedback=f"Draft contains deceptive language '{phrase}'. Speak transparently or avoid first-person customer claims.",
            )

    return None


def get_llm():
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
        return ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.0,
        )
    return None


async def critic_node(state: SwarmState) -> Dict[str, Any]:
    """
    Compliance Critic Node execution function.
    Audits the draft; returns pass/fail and corrective feedback for Drafter loop.
    """
    thread_id = state.get("thread_id", "")
    title = state.get("title", "")
    extracted_problem = state.get("extracted_problem", "")
    evidence_quote = state.get("evidence_quote", "")
    proposed_draft = state.get("proposed_draft", "")
    draft_iteration = state.get("draft_iteration", 1)

    logger.info(f"[Critic] Auditing draft for thread {thread_id}...")

    # 1. Run deterministic Guardrails checks first
    programmatic_fail = programmatic_guardrails_check(proposed_draft)
    if programmatic_fail:
        result = programmatic_fail
    else:
        # 2. Run LLM semantic compliance check
        llm = get_llm()
        if llm:
            structured_llm = llm.with_structured_output(CriticResult)
            messages = [
                SystemMessage(content=CRITIC_SYSTEM_PROMPT),
                HumanMessage(content=CRITIC_USER_PROMPT.format(
                    title=title,
                    extracted_problem=extracted_problem,
                    evidence_quote=evidence_quote,
                    proposed_draft=proposed_draft,
                )),
            ]
            result: CriticResult = await structured_llm.ainvoke(messages)
        else:
            # Deterministic pass for clean drafts in dev mode
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

    logger.info(f"[Critic] Thread {thread_id} passed: {result.critic_passed}, violation: {result.violation_category}")
    return {
        "critic_passed": result.critic_passed,
        "violation_category": result.violation_category,
        "critic_feedback": result.critic_feedback,
    }
