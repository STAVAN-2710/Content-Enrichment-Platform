"""
Business rule validation — runs after Pydantic schema enforcement.

Catches enrichments that are technically valid JSON/schema but violate domain
rules: topics outside the allowed taxonomy, missing confidence scores for key
fields, offensive summaries, or anomalously low confidence on high-quality episodes.

Returns a list of violation strings (empty = valid). The pipeline routes
violations to the dead letter queue under category 'business_rule_violation'.
"""
from typing import get_args

from src.schemas.enrichment import (
    EpisodeEnrichment,
    TopicLiteral,
)

_TOPIC_VOCABULARY: frozenset[str] = frozenset(get_args(TopicLiteral))

_REQUIRED_CONFIDENCE_KEYS = frozenset(
    {"mood", "difficulty", "primary_topics", "format", "best_listening_context"}
)

_OFFENSIVE_TERMS = frozenset({
    "nigger", "nigga", "faggot", "kike", "spic", "chink", "cunt",
})

_HIGH_QUALITY_CONFIDENCE_FLOOR = 0.4
_HIGH_QUALITY_MAX_LOW_FIELDS = 3


class ValidationError(Exception):
    pass


def validate_enrichment(enrichment: EpisodeEnrichment) -> list[str]:
    """Return list of violation descriptions; empty list means valid."""
    violations: list[str] = []

    # 1. Topic taxonomy membership
    all_topics = list(enrichment.primary_topics) + list(enrichment.secondary_topics)
    bad_topics = [t for t in all_topics if t not in _TOPIC_VOCABULARY]
    if bad_topics:
        violations.append(f"topics_not_in_vocabulary: {bad_topics}")

    # 2. Required confidence keys present
    missing_conf = _REQUIRED_CONFIDENCE_KEYS - set(enrichment.confidence_scores.keys())
    if missing_conf:
        violations.append(f"missing_confidence_scores: {sorted(missing_conf)}")

    # 3. Offensive content in summary
    summary_lower = enrichment.summary_one_sentence.lower()
    offensive = [t for t in _OFFENSIVE_TERMS if t in summary_lower]
    if offensive:
        violations.append(f"offensive_content_in_summary: {offensive}")

    # 4. High-quality episode with too many low-confidence attributes
    if enrichment.enrichment_quality == "high":
        low_conf_fields = [
            k
            for k, v in enrichment.confidence_scores.items()
            if isinstance(v, float) and v < _HIGH_QUALITY_CONFIDENCE_FLOOR
        ]
        if len(low_conf_fields) > _HIGH_QUALITY_MAX_LOW_FIELDS:
            violations.append(
                f"high_quality_episode_low_confidence: "
                f"{len(low_conf_fields)} fields below {_HIGH_QUALITY_CONFIDENCE_FLOOR}: "
                f"{low_conf_fields}"
            )

    return violations
