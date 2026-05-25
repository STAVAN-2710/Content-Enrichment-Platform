"""
Core enrichment function — takes a PodcastEpisode, calls Claude via Instructor,
returns a fully populated EpisodeEnrichment.

Instructor handles schema enforcement: if Claude returns a topic outside the
taxonomy, Instructor catches the Pydantic ValidationError, feeds it back as a
correction message, and retries (up to max_retries times in client.py).
"""
import time
from datetime import datetime, timezone

from src.enrichment.client import get_enrichment_client
from src.enrichment.prompts.v1 import PROMPT_VERSION, build_user_prompt
from src.schemas.enrichment import SCHEMA_VERSION, EpisodeEnrichment
from src.schemas.episode import PodcastEpisode


def enrich_episode(
    episode: PodcastEpisode,
    prompt_version: str = PROMPT_VERSION,
    entity_hints: list[str] | None = None,
) -> EpisodeEnrichment:
    """Enrich a single episode via Claude + Instructor.

    Returns EpisodeEnrichment with provenance fields populated.
    Raises on API failure or exhausted retries (caller handles dead letter routing).
    """
    from src.enrichment.prompts.v1 import SYSTEM_PROMPT

    client, model = get_enrichment_client()

    user_prompt = build_user_prompt(
        show_name=episode.show_name,
        text_for_enrichment=episode.text_for_enrichment,
        entity_hints=entity_hints,
    )

    start = time.perf_counter()

    enrichment: EpisodeEnrichment = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        response_model=EpisodeEnrichment,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Stamp provenance — Instructor populates the schema fields, we add metadata
    enrichment.episode_id = episode.episode_id
    enrichment.labeler = "llm"
    enrichment.labeler_confidence = None
    enrichment.prompt_version = prompt_version
    enrichment.model_used = model
    enrichment.schema_version = SCHEMA_VERSION
    enrichment.labeled_at = datetime.now(tz=timezone.utc)
    enrichment.notes = f"processing_ms={elapsed_ms:.0f}"

    return enrichment
