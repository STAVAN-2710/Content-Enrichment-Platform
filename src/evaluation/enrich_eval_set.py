"""
Enrich the golden eval set episodes using the LLM enrichment layer.

Reads episode IDs from eval_set.jsonl, fetches full episode records from
processed/episodes.jsonl, runs enrichment, writes to data/enriched/eval_enriched.jsonl.

CLI usage:
    uv run python -m src.evaluation.enrich_eval_set \
        [--eval-set data/golden/eval_set.jsonl] \
        [--processed data/processed/episodes.jsonl] \
        [--output data/enriched/eval_enriched.jsonl] \
        [--limit 10]
"""
import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

load_dotenv()

console = Console()


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open() if l.strip()]


def run(
    eval_set_path: Path,
    processed_path: Path,
    output_path: Path,
    limit: int | None = None,
) -> None:
    from src.enrichment.enricher import enrich_episode
    from src.schemas.episode import PodcastEpisode

    eval_records  = _load_jsonl(eval_set_path)
    processed_all = _load_jsonl(processed_path)

    processed_idx = {r["episode_id"]: r for r in processed_all}

    # Load already-done IDs to enable resume
    done_ids: set[str] = set()
    if output_path.exists():
        for line in output_path.open():
            if line.strip():
                done_ids.add(json.loads(line)["episode_id"])
    console.print(f"Already enriched: {len(done_ids)} / {len(eval_records)}")

    to_do = [r for r in eval_records if r["episode_id"] not in done_ids]
    if limit:
        to_do = to_do[:limit]

    if not to_do:
        console.print("[green]All eval episodes already enriched.[/green]")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[dict] = []

    with output_path.open("a") as out_f, Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Enriching eval episodes", total=len(to_do))

        for rec in to_do:
            ep_id = rec["episode_id"]
            raw = processed_idx.get(ep_id)
            if raw is None:
                console.print(f"[yellow]Episode {ep_id} not found in processed JSONL — skipping[/yellow]")
                progress.advance(task)
                continue

            try:
                episode = PodcastEpisode.model_validate(raw)
                enrichment = enrich_episode(episode)
                out_f.write(json.dumps(enrichment.model_dump(mode="json")) + "\n")
                out_f.flush()
            except Exception as exc:
                console.print(f"[red]FAILED {ep_id}: {exc}[/red]")
                errors.append({"episode_id": ep_id, "error": str(exc)})

            progress.advance(task)

    console.print(
        f"\n[bold]Done.[/bold] Enriched: {len(to_do) - len(errors)} | Errors: {len(errors)}"
    )
    if errors:
        err_path = output_path.parent / "eval_errors.jsonl"
        with err_path.open("w") as f:
            for e in errors:
                f.write(json.dumps(e) + "\n")
        console.print(f"Errors written to {err_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set",  default="data/golden/eval_set.jsonl",       type=Path)
    parser.add_argument("--processed", default="data/processed/episodes.jsonl",     type=Path)
    parser.add_argument("--output",    default="data/enriched/eval_enriched.jsonl", type=Path)
    parser.add_argument("--limit", default=None, type=int)
    args = parser.parse_args()

    run(args.eval_set, args.processed, args.output, args.limit)


if __name__ == "__main__":
    main()
