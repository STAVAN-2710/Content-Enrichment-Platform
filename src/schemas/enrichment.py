"""
EpisodeEnrichment schema — DRAFT v0 (pilot ontology, not yet frozen).
Lock this to v1 only after completing the 30-50 episode ontology pilot.
"""
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Controlled vocabularies — DRAFT, expect changes after pilot
# ---------------------------------------------------------------------------

MoodLiteral = Literal[
    "energetic", "calm", "intense", "melancholic",
    "humorous", "serious", "inspirational", "neutral",
]

ListeningContextLiteral = Literal[
    "commute", "workout", "deep_work", "casual_listening",
    "cooking", "sleep", "social", "learning",
]

TopicLiteral = Literal[
    # Technology
    "artificial_intelligence", "software_engineering", "cybersecurity",
    "hardware", "startups_and_vc", "data_science",
    "surveillance_and_privacy",
    # Science
    "neuroscience", "physics", "biology", "medicine",
    "astronomy", "climate_and_environment",
    "mathematics", "planetary_science", "paleontology",
    # Business
    "entrepreneurship", "investing", "marketing",
    "leadership", "economics", "productivity",
    # History
    "ancient_history", "modern_history", "military_history",
    "political_history", "cultural_history",
    "mythology",
    # True Crime
    "cybercrime", "true_crime",
    # Health
    "nutrition", "fitness", "mental_health", "sleep", "longevity",
    # Philosophy
    "ethics", "philosophy_of_mind", "spirituality",
    # Comedy
    "comedy", "satire",
    # Personal Development
    "relationships", "personal_finance", "career", "habits_and_mindset",
    # Culture
    "politics", "media_and_journalism", "social_issues",
    "sports", "arts_and_entertainment", "political_commentary",
]

DifficultyLiteral = Literal["beginner", "intermediate", "advanced"]

FormatLiteral = Literal[
    "interview", "solo_monologue", "panel_discussion",
    "narrative_storytelling", "debate", "educational_lecture",
]

EnrichmentQualityLiteral = Literal["high", "medium", "low"]

LabelerConfidenceLiteral = Literal["high", "medium", "low"]

LabelerLiteral = Literal["human", "llm"]

SCHEMA_VERSION = 1  # Frozen post-pilot; added mathematics, planetary_science, paleontology, mythology, surveillance_and_privacy, political_commentary


# ---------------------------------------------------------------------------
# Main enrichment record
# ---------------------------------------------------------------------------

class EpisodeEnrichment(BaseModel):
    episode_id: str

    # --- Distillable fields (student model will predict these) ---
    mood: MoodLiteral
    best_listening_context: Annotated[
        list[ListeningContextLiteral],
        Field(min_length=1, max_length=4),
    ]
    primary_topics: Annotated[
        list[TopicLiteral],
        Field(min_length=1, max_length=3),
    ]
    secondary_topics: Annotated[
        list[TopicLiteral],
        Field(max_length=5),
    ] = Field(default_factory=list)
    difficulty: DifficultyLiteral
    format: FormatLiteral

    # --- LLM-only fields (never distilled — see design doc) ---
    summary_one_sentence: Annotated[str, Field(max_length=200)]
    key_entities: Annotated[list[str], Field(max_length=10)] = Field(default_factory=list)
    content_warnings: list[str] = Field(default_factory=list)
    is_sponsored: bool = False

    # --- Quality signals ---
    enrichment_quality: EnrichmentQualityLiteral
    confidence_scores: dict[str, float] = Field(default_factory=dict)

    # --- Provenance ---
    labeler: LabelerLiteral
    labeler_confidence: Optional[LabelerConfidenceLiteral] = None  # human labels only
    notes: Optional[str] = None  # uncertainty notes from human labeler
    labeled_at: datetime = Field(default_factory=datetime.utcnow)
    prompt_version: Optional[str] = None   # set for LLM labels
    model_used: Optional[str] = None       # set for LLM labels
    schema_version: int = SCHEMA_VERSION
