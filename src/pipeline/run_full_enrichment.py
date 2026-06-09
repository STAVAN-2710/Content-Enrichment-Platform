"""
Single-threaded enrichment runner for the full corpus — bypasses Apache Beam.

Supports multi-key round-robin via OPENAI_API_KEY_1 / _2 / _3 env vars (or just
OPENAI_API_KEY for single-key). Each key gets its own rate window so N keys = N×
throughput.

CLI usage:
    PYTHONPATH=. python src/pipeline/run_full_enrichment.py \
        [--input  data/processed/episodes.jsonl] \
        [--output data/enriched/enriched_full_v5.jsonl] \
        [--failed data/enriched/failed_full_v5.jsonl] \
        [--db     data/enriched/checkpoint_full_v5.db] \
        [--limit  N]
"""
import argparse
import json
import os
from itertools import cycle
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

load_dotenv()

console = Console()
_PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v5")


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def _get_api_keys() -> list[str]:
    """Collect OPENAI_API_KEY1/2/3 then OPENAI_API_KEY from env. Skip exhausted keys."""
    keys = []
    for var in ["OPENAI_API_KEY1", "OPENAI_API_KEY2", "OPENAI_API_KEY3", "OPENAI_API_KEY"]:
        k = os.environ.get(var, "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys


def run(
    input_path: Path,
    output_path: Path,
    failed_path: Path,
    db_path: Path,
    limit: int | None = None,
) -> None:
    import instructor
    import openai

    from src.enrichment.enricher import enrich_episode
    from src.enrichment.validator import validate_enrichment
    from src.pipeline.checkpointer import Checkpointer
    from src.schemas.enrichment import SCHEMA_VERSION
    from src.schemas.episode import PodcastEpisode

    api_keys = _get_api_keys()
    if not api_keys:
        raise EnvironmentError("Set OPENAI_API_KEY (or OPENAI_API_KEY_1/2/3) in environment")

    # Build one instructor client per key; cycle through them round-robin
    clients = [
        instructor.from_openai(openai.OpenAI(api_key=k, max_retries=6))
        for k in api_keys
    ]
    key_cycle = cycle(clients)
    console.print(f"[bold]API keys:[/bold] {len(api_keys)} key(s) — round-robin enabled")

    checkpointer = Checkpointer(db_path)
    all_episodes = _load_jsonl(input_path)
    if limit:
        all_episodes = all_episodes[:limit]

    all_ids = [e["episode_id"] for e in all_episodes]
    unprocessed_ids = set(checkpointer.unprocessed_ids(all_ids))
    to_process = [e for e in all_episodes if e["episode_id"] in unprocessed_ids]

    stats = checkpointer.stats()
    console.print(
        f"[bold]Corpus enrichment[/bold] | total={len(all_episodes)} "
        f"| already_done={stats.get('success', 0)} | to_process={len(to_process)}"
    )

    if not to_process:
        console.print("[green]All episodes already processed.[/green]")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with (
        output_path.open("a") as out_f,
        failed_path.open("a") as fail_f,
        Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
        ) as progress,
    ):
        task = progress.add_task("Enriching corpus", total=len(to_process))
        n_ok = n_fail = 0

        for raw in to_process:
            ep_id = raw.get("episode_id", "unknown")
            client = next(key_cycle)
            try:
                episode = PodcastEpisode.model_validate(raw)
                enrichment = enrich_episode(episode, client=client)

                violations = validate_enrichment(enrichment)
                if violations:
                    raise ValueError(f"Validation: {'; '.join(violations)}")

                checkpointer.mark_success(ep_id, prompt_version=_PROMPT_VERSION, schema_version=SCHEMA_VERSION)
                out_f.write(json.dumps(enrichment.model_dump(mode="json")) + "\n")
                out_f.flush()
                n_ok += 1

            except Exception as exc:
                error_type = type(exc).__name__
                error_msg = str(exc)[:500]
                checkpointer.mark_failed(
                    ep_id,
                    error_type=error_type,
                    error_msg=error_msg,
                    prompt_version=_PROMPT_VERSION,
                    schema_version=SCHEMA_VERSION,
                )
                fail_f.write(json.dumps({"episode_id": ep_id, "error_type": error_type, "error_msg": error_msg}) + "\n")
                fail_f.flush()
                n_fail += 1

            progress.advance(task)

            if (n_ok + n_fail) % 500 == 0:
                console.print(f"  checkpoint: ok={n_ok} fail={n_fail}")

    console.print(f"\n[bold green]Done.[/bold green] ok={n_ok} | fail={n_fail}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="data/processed/episodes.jsonl",          type=Path)
    parser.add_argument("--output", default="data/enriched/enriched_full_v5.jsonl",   type=Path)
    parser.add_argument("--failed", default="data/enriched/failed_full_v5.jsonl",     type=Path)
    parser.add_argument("--db",     default="data/enriched/checkpoint_full_v5.db",    type=Path)
    parser.add_argument("--limit",  default=None, type=int)
    args = parser.parse_args()
    run(args.input, args.output, args.failed, args.db, args.limit)


if __name__ == "__main__":
    main()
