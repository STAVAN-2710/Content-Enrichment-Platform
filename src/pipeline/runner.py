"""
Chunked DirectRunner wrapper for local development.

DirectRunner is memory-limited — processing the full 21K-episode corpus in one
pipeline run causes memory pressure. This wrapper splits the input JSONL into
500-episode chunks, runs the Beam pipeline on each chunk sequentially, and
merges output files.

Production note: on GCP Dataflow, run build_pipeline() directly on the full
corpus — Dataflow handles horizontal scaling natively. The pipeline code is
identical; only the runner changes.

CLI usage:
    uv run python -m src.pipeline.runner \
        --input data/processed/episodes.jsonl \
        --enriched data/enriched/enriched.jsonl \
        --failed data/enriched/failed.jsonl \
        --db data/enriched/checkpoint.db \
        [--chunk-size 500] [--limit 100]
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

from src.pipeline.checkpointer import Checkpointer
from src.pipeline.pipeline import build_pipeline

console = Console()
_DEFAULT_CHUNK = 500


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open() if l.strip()]


def _write_jsonl(path: Path, records: list[dict], mode: str = "a") -> None:
    with path.open(mode) as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def run_chunked(
    input_path: Path,
    enriched_output: Path,
    failed_output: Path,
    db_path: Path,
    chunk_size: int = _DEFAULT_CHUNK,
    limit: int | None = None,
) -> None:
    checkpointer = Checkpointer(db_path)

    all_episodes = _load_jsonl(input_path)
    if limit:
        all_episodes = all_episodes[:limit]

    # Only process episodes not already successfully checkpointed
    all_ids = [e["episode_id"] for e in all_episodes]
    unprocessed_ids = set(checkpointer.unprocessed_ids(all_ids))
    to_process = [e for e in all_episodes if e["episode_id"] in unprocessed_ids]

    stats = checkpointer.stats()
    console.print(
        f"[bold]Enrichment run[/bold] | total={len(all_episodes)} | "
        f"already_done={stats.get('success', 0)} | to_process={len(to_process)}"
    )

    if not to_process:
        console.print("[green]All episodes already processed. Nothing to do.[/green]")
        return

    chunks = [
        to_process[i : i + chunk_size]
        for i in range(0, len(to_process), chunk_size)
    ]

    enriched_output.parent.mkdir(parents=True, exist_ok=True)
    failed_output.parent.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing chunks", total=len(chunks))

        for chunk_idx, chunk in enumerate(chunks):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False
            ) as tmp:
                tmp_path = Path(tmp.name)
                _write_jsonl(tmp_path, chunk, mode="w")

            chunk_enriched = enriched_output.parent / f"_chunk_{chunk_idx}_enriched.jsonl"
            chunk_failed   = enriched_output.parent / f"_chunk_{chunk_idx}_failed.jsonl"

            try:
                pipeline = build_pipeline(
                    input_path=tmp_path,
                    enriched_output=chunk_enriched,
                    failed_output=chunk_failed,
                    checkpointer=checkpointer,
                )
                pipeline.run().wait_until_finish()
            except Exception as exc:
                console.print(f"[red]Chunk {chunk_idx} pipeline error: {exc}[/red]")
            finally:
                tmp_path.unlink(missing_ok=True)

            # Merge chunk outputs into final files
            for chunk_out, final_out in [
                (chunk_enriched, enriched_output),
                (chunk_failed, failed_output),
            ]:
                if chunk_out.exists():
                    records = _load_jsonl(chunk_out)
                    if records:
                        _write_jsonl(final_out, records, mode="a")
                    chunk_out.unlink()

            progress.advance(task)

    final_stats = checkpointer.stats()
    console.print(
        f"\n[bold green]Run complete[/bold green] | "
        f"success={final_stats.get('success', 0)} | "
        f"failed={final_stats.get('failed', 0)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run chunked enrichment pipeline")
    parser.add_argument("--input",    required=True, type=Path)
    parser.add_argument("--enriched", default=Path("data/enriched/enriched.jsonl"), type=Path)
    parser.add_argument("--failed",   default=Path("data/enriched/failed.jsonl"),   type=Path)
    parser.add_argument("--db",       default=Path("data/enriched/checkpoint.db"),  type=Path)
    parser.add_argument("--chunk-size", default=_DEFAULT_CHUNK, type=int)
    parser.add_argument("--limit", default=None, type=int, help="Process only first N episodes")
    args = parser.parse_args()

    run_chunked(
        input_path=args.input,
        enriched_output=args.enriched,
        failed_output=args.failed,
        db_path=args.db,
        chunk_size=args.chunk_size,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
