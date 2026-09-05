"""
Centralized Multi-Provider LLM Factory for Dark Social Swarm.
Supports:
- Groq (Free, ultra-fast Llama-3.3-70B / Llama-3.1-8B via OpenAI-compatible API)
- OpenAI (GPT-4o, GPT-4o-mini)
- Fallback deterministic heuristic rule engines when no API key is provided
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from app.core.config import settings

logger = logging.getLogger("dark_social_swarm.llm")


def get_swarm_llm(temperature: float = 0.1, reasoning: bool = False, max_tokens: int = 450) -> Optional[ChatOpenAI]:
    """
    Returns an initialized LLM client based on configured environment keys:
    1. Groq: Free high-speed inference via https://api.groq.com/openai/v1
    2. OpenAI: GPT-4o / GPT-4o-mini
    3. None: Triggers agent deterministic rule-based fallbacks
    """
    provider = (settings.LLM_PROVIDER or "auto").lower()

    # 1. Groq Provider (Prioritized if GROQ_API_KEY is present or LLM_PROVIDER is groq)
    has_groq = bool(
        settings.GROQ_API_KEY
        and settings.GROQ_API_KEY.strip()
        and settings.GROQ_API_KEY != "your_groq_api_key_here"
    )
    if has_groq and provider in ("auto", "groq"):
        model_name = settings.GROQ_MODEL
        if not model_name or "llama" in model_name or "mixtral" in model_name or "gemma" in model_name or "compound" in model_name:
            model_name = "openai/gpt-oss-20b"

        logger.info(f"Initializing Groq LLM: {model_name} (temp={temperature}, max_tokens={max_tokens})")
        return ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=1,
            timeout=25,
        )

    # 2. OpenAI Provider
    has_openai = bool(
        settings.OPENAI_API_KEY
        and settings.OPENAI_API_KEY.strip()
        and settings.OPENAI_API_KEY != "your_openai_api_key_here"
    )
    if has_openai and provider in ("auto", "openai"):
        model_name = settings.REASONING_LLM_MODEL if reasoning else settings.DEFAULT_LLM_MODEL
        logger.debug(f"Initializing OpenAI LLM: {model_name} (temp={temperature})")
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # 3. No LLM key configured
    return None


async def invoke_structured_swarm_llm(
    schema,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    reasoning: bool = False,
    max_tokens: int = 450,
):
    """
    Invokes LLM with robust structured output parsing.
    Supports OpenAI, Groq with rate-limit backoff, and graceful heuristic fallbacks.
    """
    import asyncio
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.output_parsers import JsonOutputParser

    llm = get_swarm_llm(temperature=temperature, reasoning=reasoning, max_tokens=max_tokens)
    if not llm:
        return None

    # Try standard with_structured_output first if OpenAI native
    if settings.OPENAI_API_KEY and not settings.GROQ_API_KEY:
        try:
            structured_llm = llm.with_structured_output(schema)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            return await structured_llm.ainvoke(messages)
        except Exception as e:
            logger.warning(f"Native structured output failed: {e}. Trying parser...")

    # Universal robust JSON Parser (Works seamlessly across Groq and open-source models)
    try:
        parser = JsonOutputParser(pydantic_object=schema)
        instructions = parser.get_format_instructions()
        system_content = f"{system_prompt}\n\nIMPORTANT: Return ONLY a valid JSON object strictly matching this schema. Do not output markdown codeblocks, text, or explanations outside the JSON:\n{instructions}"
        chain = llm | parser

        for attempt in range(2):
            try:
                parsed = await chain.ainvoke([SystemMessage(content=system_content), HumanMessage(content=user_prompt)])
                if isinstance(parsed, dict):
                    return schema(**parsed)
                return parsed
            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt == 0:
                    logger.info("Groq TPM limit reached; pausing 3s for token bucket recovery before auto-retry...")
                    await asyncio.sleep(3.0)
                    continue
                # If rate limited on free tier or parsing issue, safely fall back to domain heuristics
                logger.info(f"LLM call passed to deterministic domain rules (reason: {e.__class__.__name__})")
                return None
    except Exception as e:
        logger.info(f"Structured parser fallback: {e}")
        return None
