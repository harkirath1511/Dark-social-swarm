"""
Semantic Problem-First Discovery Pre-Filter.
Difference 1: Evaluates candidate discussions strictly on problem signals, intent, and workflow friction.
STRICT RULE: Must NOT depend on brand names or competitor keywords.
"""

import re
from typing import Tuple

# Patterns indicating problem-solving, recommendation requests, alternatives search, and workflow frustration
PROBLEM_INTENT_PATTERNS = [
    # Explicit recommendation or tool seeking
    r"\b(which\s+(one|tool|app|platform|solution)\b)",
    r"\b(what\s+(is|are)\s+the\s+best\b)",
    r"\b(looking\s+for\s+(a|an|any|recommendations?|tools?|alternatives?)\b)",
    r"\b(any\s+recommendations?\b)",
    r"\b(can\s+anyone\s+recommend\b)",
    r"\b(suggest(ions?)?\s+(for|a|an)\b)",
    r"\b(alternatives?\s+(to|for)\b)",
    r"\b(how\s+do\s+(you|teams?|people)\s+(handle|solve|track|manage|deal\s+with)\b)",
    r"\b(what\s+(are\s+you|do\s+you)\s+using\s+for\b)",

    # Friction, frustration, and pain points
    r"\b(struggl(e|ing)\s+with\b)",
    r"\b(tired\s+of\b)",
    r"\b(hates?\s+(using|updating|dealing\s+with)\b)",
    r"\b(killing\s+our\b)",
    r"\b(wasting\s+(hours|time|money)\b)",
    r"\b(can'?t\s+seem\s+to\b)",
    r"\b(does(n'?t|\s+not)\s+respect|does(n'?t|\s+not)\s+work\b)",
    r"\b(cutting\s+mid-sentence|cut\s+in\s+half)\b",
    r"\b(bottleneck|friction|pain\s+point|nightmare)\b",
    r"\b(manual\s+[a-z]+\s+is\s+killing)\b",
    r"\b(tried\s+[a-z0-9]+\s+(tools|apps|solutions)\s+and\s+none)\b",
    r"\b(actually\s+works\??)\b",
]

# Negative / Promotional patterns (promotional push, spam, discount codes)
PROMOTIONAL_PATTERNS = [
    r"\b(discount\s+code|\d+%\s+off|promo\s+code|coupon)\b",
    r"\b(check\s+out\s+our\b)",
    r"\b(we\s+just\s+launched\b)",
    r"\b(dm\s+me\s+for\s+access|sign\s+up\s+now|book\s+a\s+demo)\b",
    r"\b(affiliate\s+link|buy\s+now)\b",
]

COMPILED_PROBLEM_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROBLEM_INTENT_PATTERNS]
COMPILED_PROMO_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROMOTIONAL_PATTERNS]


def evaluate_candidate_discovery(text: str) -> Tuple[bool, float]:
    """
    Evaluates raw post text (title + body) for genuine problem-seeking and friction signals.
    
    STRICT RULE:
    Zero dependency on brand or competitor names. Evaluates only behavioral intent:
    - Recommendation seeking
    - Alternatives search
    - Workflow friction / bottleneck
    - Frustration with current manual methods or flawed tooling
    
    Returns:
        (discovery_passed: bool, discovery_score: float)
        discovery_score is normalized between 0.0 and 1.0.
    """
    if not text or not text.strip():
        return False, 0.0

    lower_text = text.lower()

    # 1. Penalize obvious commercial promo / spam announcements
    promo_matches = sum(1 for pattern in COMPILED_PROMO_PATTERNS if pattern.search(lower_text))
    if promo_matches > 0:
        # Heavily penalize or reject outright
        score = max(0.0, 0.2 - (promo_matches * 0.1))
        return False, round(score, 2)

    # 2. Count problem / intent signal occurrences
    problem_matches = sum(1 for pattern in COMPILED_PROBLEM_PATTERNS if pattern.search(lower_text))

    # General interrogative boost (asking a clear question)
    has_question = "?" in text
    question_boost = 0.15 if has_question else 0.0

    # Calculate score
    base_score = 0.0
    if problem_matches >= 3:
        base_score = 0.85
    elif problem_matches == 2:
        base_score = 0.70
    elif problem_matches == 1:
        base_score = 0.55
    else:
        # Fallback keyword checks for problem indicators
        problem_keywords = ["issue", "problem", "frustrated", "bug", "broken", "help", "solve", "advice", "thoughts"]
        found_keywords = sum(1 for kw in problem_keywords if kw in lower_text)
        if found_keywords >= 2 and has_question:
            base_score = 0.50
        elif found_keywords >= 1:
            base_score = 0.35
        else:
            base_score = 0.15

    final_score = min(1.0, max(0.0, base_score + question_boost))
    passed = final_score >= 0.50

    return passed, round(final_score, 2)
