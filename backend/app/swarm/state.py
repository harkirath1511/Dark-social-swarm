"""
Master SwarmState Schema & Structured Agent Output Models.
Defines the state passed across LangGraph nodes and Pydantic schemas for serialization.
"""

from typing import TypedDict, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Pydantic Schemas for Serialization, Validation & Node Contracts
# -------------------------------------------------------------

class SwarmStateModel(BaseModel):
    """
    Pydantic schema representing the complete SwarmState.
    Used for serialization, deserialization, API payloads, and state verification.
    """
    model_config = ConfigDict(extra="ignore")

    # Input context
    platform: str = Field(default="reddit", description="Community platform source, e.g. reddit")
    thread_id: str = Field(..., description="Unique thread identifier, e.g. 't3_1h9k2z8'")
    subreddit: str = Field(..., description="Subreddit name including r/ prefix")
    title: str = Field(..., description="Post submission title")
    body: str = Field(default="", description="Post self-text body")
    author: str = Field(default="[deleted]", description="Username of the post author")
    permalink: str = Field(..., description="Canonical URL to the original thread")

    # Analyst signals
    extracted_problem: Optional[str] = Field(
        default=None,
        description="Underlying problem, friction, or technical struggle extracted by the Analyst."
    )
    user_intent: Optional[Literal["high", "medium", "low", "informational"]] = Field(
        default=None,
        description="Assessed commercial or problem-solving intent."
    )
    evidence_quote: Optional[str] = Field(
        default=None,
        description="Verbatim exact quote extracted directly from the post text."
    )

    # Strategist outputs
    opportunity_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Strategic fit score from 0 to 100. >= 40 proceeds to drafting."
    )
    engagement_decision: Optional[Literal["engage", "maybe_engage", "do_not_engage"]] = Field(
        default=None,
        description="Engagement verdict calculated by the Strategist."
    )
    strategic_reasoning: Optional[str] = Field(
        default=None,
        description="Strategic justification for the score, fit, and engagement decision."
    )

    # Drafter outputs
    proposed_draft: Optional[str] = Field(
        default=None,
        description="Authentic, value-first response drafted by Relay persona."
    )
    draft_iteration: int = Field(
        default=0,
        description="Counter tracking drafting and critique revision loops."
    )

    # Critic outputs
    critic_passed: Optional[bool] = Field(
        default=None,
        description="Whether generation passed compliance, non-astroturfing, and safety checks."
    )
    violation_category: Optional[str] = Field(
        default=None,
        description="Category of policy violation if critique failed."
    )
    critic_feedback: Optional[str] = Field(
        default=None,
        description="Actionable corrective instructions from the Critic."
    )

    # Human triage
    human_status: Optional[Literal["approved", "edited", "rejected"]] = Field(
        default=None,
        description="Human marketer review decision at the interrupt node."
    )
    final_response_text: Optional[str] = Field(
        default=None,
        description="Final approved or edited response text ready for publishing."
    )


# -------------------------------------------------------------
# Structured Output Contracts for Individual Agents
# -------------------------------------------------------------

class AnalystResult(BaseModel):
    """Output contract for Analyst Node (Scout persona)."""
    extracted_problem: str = Field(
        ...,
        description="The underlying pain point, technical struggle, or question expressed by the author."
    )
    user_intent: Literal["high", "medium", "low", "informational"] = Field(
        ...,
        description="Assessed commercial or solution-seeking intent."
    )
    evidence_quote: str = Field(
        ...,
        description="Verbatim exact quote extracted directly from the post text anchoring this opportunity."
    )


class StrategistResult(BaseModel):
    """Output contract for Strategist Node (Evaluation & Scoring)."""
    opportunity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Strategic fit score from 0 to 100. >= 40 proceeds to drafting."
    )
    engagement_decision: Literal["engage", "maybe_engage", "do_not_engage"] = Field(
        ...,
        description="Engagement recommendation."
    )
    strategic_reasoning: str = Field(
        ...,
        description="Strategic justification for the score, fit, and verdict."
    )


class DrafterResult(BaseModel):
    """Output contract for Drafting Node (Relay persona)."""
    proposed_draft: str = Field(
        ...,
        description="Value-first, direct, empathetic, and tactical response adhering to zero-plug rules."
    )


class CriticResult(BaseModel):
    """Output contract for Compliance Critic Node (Guardrails evaluation)."""
    critic_passed: bool = Field(
        ...,
        description="True if generation passes all safety, non-astroturfing, and value-first criteria."
    )
    violation_category: Optional[str] = Field(
        default=None,
        description="Category of violation (e.g., 'unsolicited_promotion', 'astroturfing', 'hallucinated_claim', 'aggressive_cta')."
    )
    critic_feedback: Optional[str] = Field(
        default=None,
        description="Actionable corrective feedback for the Drafter to repair the reply."
    )


class HumanReviewInput(BaseModel):
    """Payload provided by marketer when resuming an interrupted opportunity."""
    action: Literal["approved", "edited", "rejected"]
    final_response_text: Optional[str] = None


# -------------------------------------------------------------
# LangGraph Master State Schema (TypedDict)
# -------------------------------------------------------------

class SwarmState(TypedDict, total=False):
    """Master TypedDict state passed between nodes in the LangGraph StateGraph."""
    # Input context
    platform: str
    thread_id: str
    subreddit: str
    title: str
    body: str
    author: str
    permalink: str

    # Analyst signals
    extracted_problem: Optional[str]
    user_intent: Optional[str]
    evidence_quote: Optional[str]

    # Strategist outputs
    opportunity_score: Optional[int]
    engagement_decision: Optional[str]
    strategic_reasoning: Optional[str]

    # Drafter outputs
    proposed_draft: Optional[str]
    draft_iteration: int

    # Critic outputs
    critic_passed: Optional[bool]
    violation_category: Optional[str]
    critic_feedback: Optional[str]

    # Human triage
    human_status: Optional[str]
    final_response_text: Optional[str]
