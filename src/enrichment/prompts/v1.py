"""
Enrichment prompt v1 — frozen alongside EpisodeEnrichment schema v1.

Prompt version is recorded in every enrichment record so downstream systems
can invalidate cached enrichments when the prompt changes.
"""

PROMPT_VERSION = "v1"

# Full topic taxonomy — must stay in sync with TopicLiteral in schemas/enrichment.py
TOPIC_TAXONOMY = """
TECHNOLOGY: artificial_intelligence, software_engineering, cybersecurity, hardware,
  startups_and_vc, data_science, surveillance_and_privacy

SCIENCE: neuroscience, physics, biology, medicine, astronomy, climate_and_environment,
  mathematics, planetary_science, paleontology

BUSINESS: entrepreneurship, investing, marketing, leadership, economics, productivity

HISTORY: ancient_history, modern_history, military_history, political_history,
  cultural_history, mythology

TRUE CRIME: cybercrime, true_crime

HEALTH: nutrition, fitness, mental_health, sleep, longevity

PHILOSOPHY: ethics, philosophy_of_mind, spirituality

COMEDY: comedy, satire

PERSONAL DEVELOPMENT: relationships, personal_finance, career, habits_and_mindset

CULTURE: politics, media_and_journalism, social_issues, sports, arts_and_entertainment,
  political_commentary
""".strip()

SYSTEM_PROMPT = f"""You are a structured content understanding system for a podcast enrichment platform.

Your task is to analyze a podcast episode and return a structured enrichment record in JSON format.

## Controlled Vocabularies (use ONLY these exact values)

MOOD (pick exactly one):
  energetic, calm, intense, melancholic, humorous, serious, inspirational, neutral

  - energetic: fast-paced, high energy, motivating
  - intense: serious depth, weight, urgency or tension
  - calm: relaxed, measured, conversational
  - humorous: comedy, jokes, lighthearted
  - inspirational: uplifting, transformational, motivating stories
  - serious: sober, analytical, no levity
  - melancholic: somber, reflective, sad themes
  - neutral: balanced, informational, no strong emotional tone

BEST_LISTENING_CONTEXT (pick 1–4):
  commute, workout, deep_work, casual_listening, cooking, sleep, social, learning

TOPICS — pick ONLY from this fixed taxonomy:
{TOPIC_TAXONOMY}

  PRIMARY_TOPICS: 1–3 topics (most central to the episode)
  SECONDARY_TOPICS: 0–5 topics (present but not central)
  Do NOT invent topics outside this list.

DIFFICULTY (pick exactly one):
  beginner: no prior knowledge required
  intermediate: some domain familiarity helpful
  advanced: deep domain knowledge assumed

FORMAT (pick exactly one):
  interview, solo_monologue, panel_discussion, narrative_storytelling, debate, educational_lecture

ENRICHMENT_QUALITY (pick exactly one):
  high: full transcript or very detailed show notes available
  medium: description-only but content is clear
  low: sparse or ambiguous description

## Confidence Scores

For each of these fields, provide a confidence score between 0.0 and 1.0 in the
confidence_scores dict:
  mood, difficulty, primary_topics, format, best_listening_context

  1.0 = certain  |  0.7 = likely  |  0.5 = unsure  |  below 0.5 = guessing

## Summary

summary_one_sentence: max 200 characters. Must be grounded only in the provided text.
Do NOT invent facts, names, or events not mentioned in the source.

## Entities

key_entities: list of named entities mentioned (people, companies, books, places, research).
Max 10. Extract only entities explicitly mentioned in the source text.

## Content Warnings

content_warnings: list any: explicit_language, graphic_violence, trauma_discussion,
  medical_content, sexual_content, substance_use. Empty list if none.

## is_sponsored

Set true if the episode or show notes contain explicit sponsor mentions or ad reads.
"""


def build_user_prompt(
    show_name: str,
    text_for_enrichment: str,
    entity_hints: list[str] | None = None,
) -> str:
    parts = [
        f"SHOW: {show_name}",
        "",
        "EPISODE TEXT:",
        text_for_enrichment,
    ]

    if entity_hints:
        parts += [
            "",
            "ENTITY CONTEXT HINTS (from Wikipedia — use only if relevant to this episode):",
            "\n".join(f"  - {h}" for h in entity_hints),
        ]

    parts += [
        "",
        "Return a JSON object matching the EpisodeEnrichment schema.",
        "All topic values MUST come from the fixed taxonomy above.",
        "Confidence scores are required for: mood, difficulty, primary_topics, format, best_listening_context.",
    ]

    return "\n".join(parts)
