"""
Master SwarmState Schema & Structured Agent Output Models.
Defines the upgraded state passed across LangGraph nodes and Pydantic schemas for serialization.
"""

from typing import TypedDict, Optional, Literal, List, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator


# -------------------------------------------------------------
# Pydantic Schemas for Serialization, Validation & Node Contracts
# -------------------------------------------------------------

class SwarmStateModel(BaseModel):
    """
    Pydantic schema representing the complete SwarmState.
    Used for serialization, deserialization, API payloads, and state verification.
    """
    model_config = ConfigDict(extra="ignore")

    # Platform Ingestion (Platform-agnostic)
    platform: str = Field(default="reddit", description="Community platform source, e.g. reddit")
    thread_id: str = Field(..., description="Unique thread identifier, e.g. 't3_1h9k2z8'")
    community_id: Optional[str] = Field(default=None, description="Subreddit name or community channel")
    subreddit: Optional[str] = Field(default=None, description="Subreddit alias for backward compatibility")
    title: str = Field(..., description="Post submission title")
    body: str = Field(default="", description="Post self-text body")
    author: str = Field(default="[deleted]", description="Username of the post author")
    permalink: str = Field(..., description="Canonical URL to the original thread")
    created_utc: float = Field(default=0.0, description="Creation timestamp UTC")

    @model_validator(mode="before")
    @classmethod
    def populate_community_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("community_id"):
                data["community_id"] = data.get("subreddit") or "r/general"
        return data

    # Candidate Discovery
    discovery_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Problem-seeking score (0.0 - 1.0)")
    discovery_passed: bool = Field(default=True, description="Whether the post passed problem discovery pre-filter")

    # Analyst Outputs
    extracted_problem: Optional[str] = Field(default=None, description="Extracted problem/struggle")
    pain_point: Optional[str] = Field(default=None, description="Underlying operational/emotional friction")
    conversation_context: Optional[str] = Field(default=None, description="Discussion context and nuances")
    community_context: Optional[str] = Field(default=None, description="Community norms and rules context")
    user_goal: Optional[str] = Field(default=None, description="What the user aims to accomplish")
    user_intent: Optional[Literal[
        "recommendation_seeking",
        "alternative_seeking",
        "troubleshooting",
        "workflow_friction",
        "educational",
        "general_discussion",
        "high", "medium", "low", "informational"  # backward compatibility
    ]] = Field(default="general_discussion", description="Assessed commercial or solution-seeking intent")
    sentiment: Optional[Literal["frustrated", "curious", "skeptical", "neutral", "positive"]] = Field(
        default="neutral", description="Detected emotional tone of the post"
    )
    entities: List[str] = Field(default_factory=list, description="Extracted domain entities and tech tools")
    brand_mentioned: bool = Field(default=False, description="Whether our brand was explicitly mentioned")
    competitor_mentioned: bool = Field(default=False, description="Whether competitors were mentioned")
    mentioned_brands: List[str] = Field(default_factory=list, description="List of recognized brands")
    mentioned_competitors: List[str] = Field(default_factory=list, description="List of recognized competitors")
    evidence_quote: Optional[str] = Field(default=None, description="Primary verbatim anchor quote")
    evidence: List[str] = Field(default_factory=list, description="Structured array of observable verbatim quotes")
    analyst_confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Analyst confidence score")

    # Strategist 6D Outputs
    relevance_score: Optional[int] = Field(default=None, ge=0, le=100, description="Domain solution fit (0-100)")
    intent_strength_score: Optional[int] = Field(default=None, ge=0, le=100, description="Intent clarity and urgency (0-100)")
    community_fit_score: Optional[int] = Field(default=None, ge=0, le=100, description="Community receptivity (0-100)")
    credibility_score: Optional[int] = Field(default=None, ge=0, le=100, description="Authenticity of user struggle (0-100)")
    engagement_risk_score: Optional[int] = Field(default=None, ge=0, le=100, description="Backlash or spam risk (0-100)")
    opportunity_score: Optional[int] = Field(default=None, ge=0, le=100, description="Composite weighted score (0-100)")
    strategist_confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Strategist confidence score")
    engagement_decision: Optional[Literal["engage", "maybe_engage", "do_not_engage"]] = Field(
        default=None, description="Strategic engagement verdict"
    )
    strategic_reasoning: Optional[str] = Field(default=None, description="Why this user / community / now")

    # Sensitive Topic Safety Gate
    sensitive_topic: bool = Field(default=False, description="Whether topic is medical, legal, crisis, or toxic")
    sensitive_topic_reason: Optional[str] = Field(default=None, description="Reason for sensitive classification")

    # Drafter Outputs
    proposed_draft: Optional[str] = Field(default=None, description="Value-first zero-plug proposed draft")
    draft_iteration: int = Field(default=0, description="Number of drafting iterations")

    # Critic Outputs
    critic_passed: Optional[bool] = Field(default=None, description="Whether draft passed compliance audit")
    violation_category: Optional[Literal[
        "astroturfing",
        "unsupported_claims",
        "excessive_promotion",
        "community_rule_violation",
        "off_topic"
    ]] = Field(default=None, description="Category of violation if audit failed")
    critic_feedback: Optional[str] = Field(default=None, description="Corrective feedback for drafter")

    # Human Triage & Structured Rejection
    human_status: Optional[Literal["approved", "edited", "rejected"]] = Field(
        default=None, description="Marketer triage verdict"
    )
    rejection_reason: Optional[Literal[
        "wrong_community",
        "too_promotional",
        "low_intent",
        "unsafe_topic",
        "not_relevant",
        "poor_evidence"
    ]] = Field(default=None, description="Structured calibration reason for rejection")
    final_response_text: Optional[str] = Field(default=None, description="Final response authorized for publication")


# -------------------------------------------------------------
# Structured Output Contracts for Individual Agents
# -------------------------------------------------------------

class AnalystResult(BaseModel):
    """Output contract for Analyst Node (Scout persona)."""
    model_config = ConfigDict(extra="ignore")
    extracted_problem: str = Field(..., description="Core struggle or problem identified")
    pain_point: str = Field(default="Friction in current workflow", description="Underlying operational or emotional friction")
    conversation_context: str = Field(default="Community thread discussion", description="Context of the conversation and thread nuances")
    community_context: str = Field(default="", description="Community norms and posting tolerance")
    user_goal: str = Field(default="Find viable solution or advice", description="What the user wants to accomplish")
    user_intent: Literal[
        "recommendation_seeking",
        "alternative_seeking",
        "troubleshooting",
        "workflow_friction",
        "educational",
        "general_discussion",
        "high", "medium", "low", "informational"
    ] = Field(default="general_discussion", description="Classified intent")
    sentiment: Literal["frustrated", "curious", "skeptical", "neutral", "positive"] = Field(
        default="neutral", description="Observed sentiment"
    )
    entities: List[str] = Field(default_factory=list, description="Extracted domain entities and tech tools")
    brand_mentioned: bool = Field(default=False, description="Whether our brand was mentioned")
    competitor_mentioned: bool = Field(default=False, description="Whether competitors were mentioned")
    mentioned_brands: List[str] = Field(default_factory=list, description="Identified brand names")
    mentioned_competitors: List[str] = Field(default_factory=list, description="Identified competitor names")
    evidence_quote: str = Field(..., description="Primary anchor quote verbatim from post")
    evidence: List[str] = Field(default_factory=list, description="Multiple verbatim observable quotes")
    analyst_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Analyst confidence")


class StrategistResult(BaseModel):
    """Output contract for Strategist Node (6-Dimensional Evaluation)."""
    model_config = ConfigDict(extra="ignore")
    relevance_score: int = Field(default=85, ge=0, le=100, description="Domain solution fit")
    intent_strength_score: int = Field(default=85, ge=0, le=100, description="Commercial/recommendation urgency")
    community_fit_score: int = Field(default=80, ge=0, le=100, description="Community tolerance for answers")
    credibility_score: int = Field(default=85, ge=0, le=100, description="Authenticity of user post")
    engagement_risk_score: int = Field(default=20, ge=0, le=100, description="Risk of backlash or spam perception")
    opportunity_score: int = Field(..., ge=0, le=100, description="Composite weighted score")
    strategist_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Evaluation confidence")
    engagement_decision: Literal["engage", "maybe_engage", "do_not_engage"] = Field(
        ..., description="Engagement decision"
    )
    strategic_reasoning: str = Field(..., description="Why this user / community / now")


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
    violation_category: Optional[Literal[
        "astroturfing",
        "unsupported_claims",
        "excessive_promotion",
        "community_rule_violation",
        "off_topic"
    ]] = Field(
        default=None,
        description="Category of violation if audit failed."
    )
    critic_feedback: Optional[str] = Field(
        default=None,
        description="Actionable corrective feedback for the Drafter to repair the reply."
    )


class HumanReviewInput(BaseModel):
    """Payload provided by marketer when resuming an interrupted opportunity."""
    action: Literal["approved", "edited", "rejected"]
    rejection_reason: Optional[Literal[
        "wrong_community",
        "too_promotional",
        "low_intent",
        "unsafe_topic",
        "not_relevant",
        "poor_evidence"
    ]] = None
    final_response_text: Optional[str] = None


# -------------------------------------------------------------
# LangGraph Master State Schema (TypedDict)
# -------------------------------------------------------------

class SwarmState(TypedDict, total=False):
    """Master TypedDict state passed between nodes in the LangGraph StateGraph."""
    # Platform Ingestion (Make platform-agnostic)
    platform: str
    thread_id: str
    community_id: str           # Subreddit name or community channel
    subreddit: str              # Alias for backward compatibility
    title: str
    body: str
    author: str
    permalink: str
    created_utc: float

    # Difference 1: Candidate Discovery
    discovery_score: float      # Problem-seeking score (0.0 - 1.0)
    discovery_passed: bool

    # Differences 2, 3, 5, 7, 9: Analyst Outputs
    extracted_problem: str
    pain_point: str
    conversation_context: str
    community_context: str      # Subreddit rules and posting norms
    user_goal: str
    user_intent: Literal[
        "recommendation_seeking",
        "alternative_seeking",
        "troubleshooting",
        "workflow_friction",
        "educational",
        "general_discussion"
    ]
    sentiment: Literal["frustrated", "curious", "skeptical", "neutral", "positive"]
    entities: list[str]
    brand_mentioned: bool
    competitor_mentioned: bool
    mentioned_brands: list[str]
    mentioned_competitors: list[str]
    evidence_quote: str         # Primary anchor quote
    evidence: list[str]         # Structured array of observable verbatim evidence quotes
    analyst_confidence: float   # 0.0 to 1.0

    # Differences 4, 6, 7, 8, 16: Strategist 6D Outputs
    relevance_score: int        # 0 to 100
    intent_strength_score: int  # 0 to 100
    community_fit_score: int    # 0 to 100
    credibility_score: int      # 0 to 100
    engagement_risk_score: int  # 0 to 100 (higher = riskier)
    opportunity_score: int      # 0 to 100 (composite)
    strategist_confidence: float# 0.0 to 1.0
    engagement_decision: Literal["engage", "maybe_engage", "do_not_engage"]
    strategic_reasoning: str    # Why this user / Why this community / Why now

    # Difference 10: Sensitive Topic Safety Gate
    sensitive_topic: bool
    sensitive_topic_reason: Optional[str]

    # Differences 17, 18: Drafting Agent Outputs
    proposed_draft: str
    draft_iteration: int

    # Differences 11, 12: Compliance Critic Outputs
    critic_passed: bool
    violation_category: Optional[Literal[
        "astroturfing",
        "unsupported_claims",
        "excessive_promotion",
        "community_rule_violation",
        "off_topic"
    ]]
    critic_feedback: Optional[str]

    # Differences 13, 14: Human Triage & Structured Rejection
    human_status: Optional[Literal["approved", "edited", "rejected"]]
    rejection_reason: Optional[Literal[
        "wrong_community",
        "too_promotional",
        "low_intent",
        "unsafe_topic",
        "not_relevant",
        "poor_evidence"
    ]]
    final_response_text: Optional[str]
