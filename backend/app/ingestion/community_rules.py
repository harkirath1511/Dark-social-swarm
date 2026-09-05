"""
Community Norms & Rules Registry.
Difference 8: Maps community IDs/subreddits to their cultural norms, promotional tolerance, and moderation scrutiny.
Used by Analyst and Strategist to calibrate community fit and engagement risk.
"""

from typing import Dict, Any

COMMUNITY_NORMS: Dict[str, Dict[str, Any]] = {
    "r/webdev": {
        "scrutiny_level": "extreme",
        "promo_tolerance": "zero_tolerance",
        "description": "Technical web development community with strict moderation. Self-promotion, affiliate links, and unsolicited tool plugs lead to immediate bans. Only in-depth technical explanations, code snippets, or architectural solutions are tolerated.",
        "recommended_approach": "Answer with pure technical depth, code or architecture first. Do not mention tools unless directly asked for stack alternatives.",
        "fit_modifier": 0.6,
        "risk_modifier": 1.4,
    },
    "r/SaaS": {
        "scrutiny_level": "moderate",
        "promo_tolerance": "moderate",
        "description": "Founders, operators, and growth practitioners discussing SaaS software, workflows, and architectures. Tool recommendations are welcome if relevant and solving an explicit operational bottleneck.",
        "recommended_approach": "Provide empathetic founder-to-founder workflow advice. Discuss methodology before mentioning tooling.",
        "fit_modifier": 1.0,
        "risk_modifier": 0.8,
    },
    "r/startups": {
        "scrutiny_level": "high",
        "promo_tolerance": "low_to_moderate",
        "description": "Startup founders and early team members. Highly vigilant against thinly veiled self-promotion or cold outreach. Appreciates direct experience, post-mortems, and actionable tactical workflows.",
        "recommended_approach": "Focus on business mechanics, team productivity, or operational leverage. Ground answers in genuine startup challenges.",
        "fit_modifier": 0.9,
        "risk_modifier": 1.1,
    },
    "r/videoediting": {
        "scrutiny_level": "high",
        "promo_tolerance": "low",
        "description": "Video editors and content creators. Strict rules regarding software spam and AI buzzwords. Only practical, hands-on workflow and codec/timeline advice is valued.",
        "recommended_approach": "Address audio/video editing mechanics directly (e.g. cadence, cuts, timestamps). Never push AI tools as magic fixes.",
        "fit_modifier": 0.85,
        "risk_modifier": 1.2,
    },
    "r/productivity": {
        "scrutiny_level": "moderate",
        "promo_tolerance": "moderate",
        "description": "Individuals optimizing personal and team workflows. Open to new tools and systems if they eliminate repetitive friction.",
        "recommended_approach": "Share systems and organizational philosophies before specific software solutions.",
        "fit_modifier": 0.95,
        "risk_modifier": 0.9,
    },
    "r/Entrepreneur": {
        "scrutiny_level": "moderate",
        "promo_tolerance": "moderate",
        "description": "Broad entrepreneurship forum. Sensitive to dropship/guru spam, but receptive to concrete solutions for lead gen, CRM friction, and operations.",
        "recommended_approach": "Deliver no-BS operational insight. Avoid buzzwords and hype.",
        "fit_modifier": 0.9,
        "risk_modifier": 1.0,
    },
    "r/smallbusiness": {
        "scrutiny_level": "moderate",
        "promo_tolerance": "low_to_moderate",
        "description": "Brick-and-mortar and digital small business owners. Value simple, reliable, cost-effective solutions over complex enterprise tooling.",
        "recommended_approach": "Keep advice practical, non-technical, and focused on cost/time savings.",
        "fit_modifier": 0.9,
        "risk_modifier": 1.0,
    },
}

DEFAULT_COMMUNITY_NORM: Dict[str, Any] = {
    "scrutiny_level": "moderate",
    "promo_tolerance": "low_to_moderate",
    "description": "Public online community. Presume standard anti-spam moderation and high sensitivity to self-promotion.",
    "recommended_approach": "Provide value-first educational content. Avoid marketing claims.",
    "fit_modifier": 0.8,
    "risk_modifier": 1.0,
}


def normalize_community_id(community_id: str) -> str:
    """Normalize subreddit or community channel string (e.g. 'SaaS' -> 'r/SaaS')."""
    if not community_id:
        return "r/general"
    clean = community_id.strip()
    if clean.startswith("r/") or clean.startswith("#"):
        return clean
    return f"r/{clean}"


def get_community_rules(community_id: str) -> Dict[str, Any]:
    """Retrieve structured rules and moderation parameters for a community."""
    cid = normalize_community_id(community_id)
    return COMMUNITY_NORMS.get(cid, DEFAULT_COMMUNITY_NORM)


def get_community_context(community_id: str) -> str:
    """
    Returns human/LLM-readable community context string describing norms and tolerance.
    """
    rules = get_community_rules(community_id)
    cid = normalize_community_id(community_id)
    return (
        f"[{cid} Norms] Scrutiny: {rules['scrutiny_level']}, "
        f"Promo Tolerance: {rules['promo_tolerance']}. "
        f"{rules['description']} Best practice: {rules['recommended_approach']}"
    )
