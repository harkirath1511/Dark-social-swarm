"""
Drafting Agent Node (Relay Persona).
Crafts value-first, context-aware, zero-plug replies adhering to community norms.
"""

import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.swarm.state import SwarmState, DrafterResult
from app.swarm.prompts.drafter import DRAFTER_SYSTEM_PROMPT, DRAFTER_USER_PROMPT

logger = logging.getLogger("dark_social_swarm.agents.drafter")


def get_llm():
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
        return ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
        )
    return None


async def drafter_node(state: SwarmState) -> Dict[str, Any]:
    """
    Drafter Node execution function.
    Drafts authentic peer response. Addresses previous critic feedback if in revision loop.
    """
    thread_id = state.get("thread_id", "")
    subreddit = state.get("subreddit", "")
    author = state.get("author", "")
    title = state.get("title", "")
    extracted_problem = state.get("extracted_problem", "")
    evidence_quote = state.get("evidence_quote", "")
    critic_feedback = state.get("critic_feedback")
    current_iteration = state.get("draft_iteration", 0) + 1

    logger.info(f"[Drafter] Drafting response for {thread_id} (Iteration {current_iteration})...")

    critic_section = (
        f"PREVIOUS COMPLIANCE AUDIT FEEDBACK (MUST ADDRESS):\n{critic_feedback}\n"
        if critic_feedback
        else "No previous compliance issues."
    )

    llm = get_llm()
    if llm:
        structured_llm = llm.with_structured_output(DrafterResult)
        messages = [
            SystemMessage(content=DRAFTER_SYSTEM_PROMPT),
            HumanMessage(content=DRAFTER_USER_PROMPT.format(
                subreddit=subreddit,
                author=author,
                title=title,
                extracted_problem=extracted_problem,
                evidence_quote=evidence_quote,
                strategic_context=state.get("strategic_reasoning", ""),
                critic_feedback_section=critic_section,
            )),
        ]
        result: DrafterResult = await structured_llm.ainvoke(messages)
        draft_text = result.proposed_draft
    else:
        # Fallback value-first draft generation for offline testing
        draft_text = (
            f"The primary reason this happens is how tools handle boundary segmentation.\n\n"
            f"If you're looking at alternatives, the cleanest architectural fix is pairing timestamp-based "
            f"token boundaries rather than relying on raw silence thresholds. This ensures cuts don't slice words "
            f"in half while preserving conversational flow."
        )

    logger.info(f"[Drafter] Generated draft for {thread_id} ({len(draft_text)} chars)")
    return {
        "proposed_draft": draft_text,
        "draft_iteration": current_iteration,
    }
