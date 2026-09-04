"""
Analyst Agent Node (Scout Persona).
Extracts the underlying problem, buying intent, and verbatim evidence quote.
"""

import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import update_analyst_signals
from app.swarm.state import SwarmState, AnalystResult
from app.swarm.prompts.analyst import ANALYST_SYSTEM_PROMPT, ANALYST_USER_PROMPT

logger = logging.getLogger("dark_social_swarm.agents.analyst")


def get_llm():
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
        return ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1,
        )
    return None


async def analyst_node(state: SwarmState) -> Dict[str, Any]:
    """
    Analyst Node execution function.
    Parses thread context, identifies core problem, assesses intent, and extracts verbatim quote.
    """
    thread_id = state.get("thread_id", "")
    subreddit = state.get("subreddit", "")
    title = state.get("title", "")
    body = state.get("body", "")
    author = state.get("author", "")

    logger.info(f"[Analyst] Analyzing thread {thread_id} in {subreddit}...")

    llm = get_llm()
    if llm:
        structured_llm = llm.with_structured_output(AnalystResult)
        messages = [
            SystemMessage(content=ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=ANALYST_USER_PROMPT.format(
                subreddit=subreddit,
                author=author,
                title=title,
                body=body or "(No self-text, title only)"
            )),
        ]
        result: AnalystResult = await structured_llm.ainvoke(messages)
    else:
        # Deterministic heuristic extraction for dev/test mode without API keys
        evidence = body.split(".")[0].strip() if body and "." in body else title
        if not evidence:
            evidence = title
        result = AnalystResult(
            extracted_problem=f"Struggle identified in post: {title}",
            user_intent="high" if any(w in (title + body).lower() for w in ["which one", "tool", "crm", "workflow", "looking for"]) else "medium",
            evidence_quote=evidence[:150],
        )

    # Persist findings to database
    await update_analyst_signals(
        thread_id=thread_id,
        extracted_problem=result.extracted_problem,
        user_intent=result.user_intent,
        evidence_quote=result.evidence_quote,
    )

    logger.info(f"[Analyst] Thread {thread_id} intent: {result.user_intent}")
    return {
        "extracted_problem": result.extracted_problem,
        "user_intent": result.user_intent,
        "evidence_quote": result.evidence_quote,
    }
