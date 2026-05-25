"""
Apache Beam enrichment pipeline — 4-stage DAG.

Stages:
  1. Read & parse episodes from JSONL
  2. Filter already-processed episodes (checkpointer)
  3. Batch episodes (reduces API call overhead)
  4. Enrich + validate, routing to 'enriched' or 'failed' tagged outputs

Runs on DirectRunner locally. The pipeline code is identical for Dataflow —
only the runner configuration changes. The chunked runner in runner.py handles
DirectRunner's memory limit for local development.
"""
import json
import traceback
from pathlib import Path
from typing import Any

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from src.enrichment.enricher import enrich_episode
from src.enrichment.prompts.v1 import PROMPT_VERSION
from src.pipeline.checkpointer import Checkpointer
from src.schemas.enrichment import SCHEMA_VERSION, EpisodeEnrichment
from src.schemas.episode import PodcastEpisode

_ENRICHED_TAG = "enriched"
_FAILED_TAG = "failed"


class _FilterProcessed(beam.DoFn):
    def __init__(self, checkpointer: Checkpointer) -> None:
        self._checkpointer = checkpointer

    def process(self, element: dict) -> Any:
        if not self._checkpointer.is_processed(element["episode_id"]):
            yield element


class _EnrichDoFn(beam.DoFn):
    def __init__(self, checkpointer: Checkpointer) -> None:
        self._checkpointer = checkpointer

    def process(self, batch: list[dict]) -> Any:
        for raw in batch:
            episode_id = raw.get("episode_id", "unknown")
            try:
                episode = PodcastEpisode.model_validate(raw)
                enrichment = enrich_episode(episode)
                self._checkpointer.mark_success(
                    episode_id,
                    prompt_version=PROMPT_VERSION,
                    schema_version=SCHEMA_VERSION,
                )
                yield beam.pvalue.TaggedOutput(
                    _ENRICHED_TAG, enrichment.model_dump(mode="json")
                )
            except Exception as exc:
                error_type = type(exc).__name__
                error_msg = f"{exc}\n{traceback.format_exc()[-500:]}"
                self._checkpointer.mark_failed(
                    episode_id,
                    error_type=error_type,
                    error_msg=error_msg,
                    prompt_version=PROMPT_VERSION,
                    schema_version=SCHEMA_VERSION,
                )
                yield beam.pvalue.TaggedOutput(
                    _FAILED_TAG,
                    {
                        "episode_id": episode_id,
                        "error_type": error_type,
                        "error_msg": error_msg,
                        "failure_category": "llm_failure",
                        "raw_episode": raw,
                    },
                )


class _ValidateDoFn(beam.DoFn):
    """Post-schema business rule validation — routes violations to dead letter."""

    def __init__(self, checkpointer: Checkpointer) -> None:
        self._checkpointer = checkpointer

    def process(self, element: dict) -> Any:
        from src.enrichment.validator import validate_enrichment, ValidationError

        episode_id = element.get("episode_id", "unknown")
        try:
            enrichment = EpisodeEnrichment.model_validate(element)
            violations = validate_enrichment(enrichment)
            if violations:
                self._checkpointer.mark_failed(
                    episode_id,
                    error_type="business_rule_violation",
                    error_msg="; ".join(violations),
                    prompt_version=element.get("prompt_version"),
                    schema_version=element.get("schema_version"),
                )
                yield beam.pvalue.TaggedOutput(
                    _FAILED_TAG,
                    {
                        "episode_id": episode_id,
                        "error_type": "business_rule_violation",
                        "error_msg": "; ".join(violations),
                        "failure_category": "business_rule_violation",
                        "raw_enrichment": element,
                    },
                )
            else:
                yield beam.pvalue.TaggedOutput(_ENRICHED_TAG, element)
        except Exception as exc:
            yield beam.pvalue.TaggedOutput(
                _FAILED_TAG,
                {
                    "episode_id": episode_id,
                    "error_type": type(exc).__name__,
                    "error_msg": str(exc),
                    "failure_category": "validation_error",
                    "raw_enrichment": element,
                },
            )


class _WriteJsonl(beam.DoFn):
    def __init__(self, output_path: Path) -> None:
        self._output_path = str(output_path)
        self._fh = None

    def start_bundle(self):
        self._fh = open(self._output_path, "a")

    def process(self, element: dict) -> None:
        self._fh.write(json.dumps(element) + "\n")

    def finish_bundle(self):
        if self._fh:
            self._fh.close()


def build_pipeline(
    input_path: Path,
    enriched_output: Path,
    failed_output: Path,
    checkpointer: Checkpointer,
    pipeline_options: PipelineOptions | None = None,
    batch_size: int = 10,
) -> beam.Pipeline:
    """Construct the enrichment pipeline. Call .run() on the returned pipeline."""
    options = pipeline_options or PipelineOptions(runner="DirectRunner")

    p = beam.Pipeline(options=options)

    episodes = (
        p
        | "ReadEpisodes" >> beam.io.ReadFromText(str(input_path))
        | "ParseJson" >> beam.Map(json.loads)
        | "FilterProcessed" >> beam.ParDo(_FilterProcessed(checkpointer))
    )

    enrich_results = (
        episodes
        | "BatchEpisodes" >> beam.BatchElements(
            min_batch_size=1, target_batch_overhead=0.05, target_batch_size=batch_size
        )
        | "EnrichBatch" >> beam.ParDo(
            _EnrichDoFn(checkpointer)
        ).with_outputs(_FAILED_TAG, main=_ENRICHED_TAG)
    )

    validate_results = (
        enrich_results[_ENRICHED_TAG]
        | "ValidateEnrichments" >> beam.ParDo(
            _ValidateDoFn(checkpointer)
        ).with_outputs(_FAILED_TAG, main=_ENRICHED_TAG)
    )

    (
        validate_results[_ENRICHED_TAG]
        | "WriteEnriched" >> beam.ParDo(_WriteJsonl(enriched_output))
    )

    (
        (enrich_results[_FAILED_TAG], validate_results[_FAILED_TAG])
        | "FlattenFailed" >> beam.Flatten()
        | "WriteFailed" >> beam.ParDo(_WriteJsonl(failed_output))
    )

    return p
