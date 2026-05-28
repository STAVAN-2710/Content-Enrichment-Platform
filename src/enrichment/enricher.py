"""
Core enrichment function — takes a PodcastEpisode, calls the LLM via Instructor,
returns a fully populated EpisodeEnrichment.

Instructor handles schema enforcement: if the model returns a topic outside the
taxonomy, Instructor catches the Pydantic ValidationError, feeds it back as a
correction message, and retries (up to max_retries times in client.py).
"""
import importlib
import os
import time
from datetime import datetime, timezone

from src.enrichment.client import MAX_RETRIES, get_enrichment_client
from src.schemas.enrichment import SCHEMA_VERSION, EpisodeEnrichment
from src.schemas.episode import PodcastEpisode

_PROMPT_MODULES = {
    "v1": "src.enrichment.prompts.v1",
    "v2": "src.enrichment.prompts.v2",
}
_DEFAULT_PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v2")


def _load_prompt(version: str):
    module_path = _PROMPT_MODULES.get(version)
    if module_path is None:
        raise ValueError(f"Unknown prompt version: {version!r}. Valid: {list(_PROMPT_MODULES)}")
    return importlib.import_module(module_path)


def enrich_episode(
    episode: PodcastEpisode,
    prompt_version: str | None = None,
    entity_hints: list[str] | None = None,
) -> EpisodeEnrichment:
    """Enrich a single episode via LLM + Instructor.

    Returns EpisodeEnrichment with provenance fields populated.
    Raises on API failure or exhausted retries (caller handles dead letter routing).
    """
    resolved_version = prompt_version or _DEFAULT_PROMPT_VERSION
    prompt_module = _load_prompt(resolved_version)
    SYSTEM_PROMPT = prompt_module.SYSTEM_PROMPT
    build_user_prompt = prompt_module.build_user_prompt

    client, model = get_enrichment_client()

    user_prompt = build_user_prompt(
        show_name=episode.show_name,
        text_for_enrichment=episode.text_for_enrichment,
        entity_hints=entity_hints,
    )

    start = time.perf_counter()

    enrichment: EpisodeEnrichment = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_model=EpisodeEnrichment,
        max_retries=MAX_RETRIES,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Stamp provenance — Instructor populates the schema fields, we add metadata
    enrichment.episode_id = episode.episode_id
    enrichment.labeler = "llm"
    enrichment.labeler_confidence = None
    enrichment.prompt_version = resolved_version
    enrichment.model_used = model
    enrichment.schema_version = SCHEMA_VERSION
    enrichment.labeled_at = datetime.now(tz=timezone.utc)
    enrichment.notes = f"processing_ms={elapsed_ms:.0f}"

    return enrichment
