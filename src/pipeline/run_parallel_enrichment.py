"""
1-thread-per-key parallel enrichment runner.

Each API key gets its own dedicated worker thread so quotas never contend.
Supports both OpenAI keys and an Azure key as separate threads with independent
quota pools. A per-thread sleep throttles OpenAI org-level RPD consumption.

CLI usage:
    PYTHONPATH=. python src/pipeline/run_parallel_enrichment.py \
        [--input  data/processed/episodes.jsonl] \
        [--output data/enriched/enriched_full_v5.jsonl] \
        [--failed data/enriched/failed_full_v5.jsonl] \
        [--db     data/enriched/checkpoint_full_v5.db] \
        [--limit  N]

Keys read from env: OPENAI_API_KEY1 … OPENAI_API_KEY8, then OPENAI_API_KEY.
Azure: AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT.
Add keys to .env and relaunch — no code changes needed.
"""
import argparse
import json
import os
import queue
import time
import threading
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

load_dotenv()

console = Console()
_PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v5")
_SENTINEL = None  # signals worker threads to stop


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def _get_openai_keys() -> list[str]:
    keys = []
    for var in [
        "OPENAI_API_KEY1", "OPENAI_API_KEY2", "OPENAI_API_KEY3", "OPENAI_API_KEY4",
        "OPENAI_API_KEY5", "OPENAI_API_KEY6", "OPENAI_API_KEY7", "OPENAI_API_KEY8",
        "OPENAI_API_KEY",
    ]:
        k = os.environ.get(var, "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys


def _get_azure_client():
    """Return (instructor_client, deployment_name) for Azure, or None if not configured."""
    import instructor
    import openai

    azure_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    if not azure_key:
        return None, None
    endpoint = (os.environ.get("AZURE_OPENAI_ENDPOINT") or os.environ.get("AZURE_OPENAI_BASE_URL", "")).rstrip("/")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    raw = openai.OpenAI(api_key=azure_key, base_url=endpoint, max_retries=3)
    return instructor.from_openai(raw), deployment


def _worker(
    client,
    model: str,
    key_label: str,
    ep_queue: queue.Queue,
    checkpointer,
    out_lock: threading.Lock,
    out_f,
    fail_f,
    schema_version: int,
    counters: dict,
    counter_lock: threading.Lock,
    progress,
    task_id,
    sleep_between: float = 0.0,
) -> None:
    from src.enrichment.enricher import enrich_episode
    from src.enrichment.validator import validate_enrichment
    from src.schemas.episode import PodcastEpisode

    while True:
        raw = ep_queue.get()
        if raw is _SENTINEL:
            ep_queue.put(_SENTINEL)  # re-queue so other workers also stop
            break

        ep_id = raw.get("episode_id", "unknown")
        try:
            episode = PodcastEpisode.model_validate(raw)
            enrichment = enrich_episode(episode, client=client)

            violations = validate_enrichment(enrichment)
            if violations:
                raise ValueError(f"Validation: {'; '.join(violations)}")

            checkpointer.mark_success(ep_id, prompt_version=_PROMPT_VERSION, schema_version=schema_version)
            with out_lock:
                out_f.write(json.dumps(enrichment.model_dump(mode="json")) + "\n")
                out_f.flush()

            with counter_lock:
                counters["ok"] += 1

        except Exception as exc:
            error_type = type(exc).__name__
            error_msg = str(exc)[:500]
            checkpointer.mark_failed(
                ep_id,
                error_type=error_type,
                error_msg=error_msg,
                prompt_version=_PROMPT_VERSION,
                schema_version=schema_version,
            )
            with out_lock:
                fail_f.write(json.dumps({"episode_id": ep_id, "error_type": error_type, "error_msg": error_msg}) + "\n")
                fail_f.flush()

            with counter_lock:
                counters["fail"] += 1

        progress.advance(task_id)

        with counter_lock:
            done = counters["ok"] + counters["fail"]
        if done % 500 == 0 and done > 0:
            with counter_lock:
                ok, fail = counters["ok"], counters["fail"]
            console.print(f"  [{key_label}] checkpoint: ok={ok} fail={fail}")

        if sleep_between > 0:
            time.sleep(sleep_between)

        ep_queue.task_done()


def run(
    input_path: Path,
    output_path: Path,
    failed_path: Path,
    db_path: Path,
    limit: int | None = None,
    openai_sleep: float = 3.0,
) -> None:
    """
    openai_sleep: seconds to sleep after each OpenAI request (per thread).
    Set to 0 to disable throttling (risks RPD exhaustion).
    Azure thread always runs without sleep (separate quota).
    """
    import instructor
    import openai as openai_lib

    from src.pipeline.checkpointer import Checkpointer
    from src.schemas.enrichment import SCHEMA_VERSION

    # Build worker specs: list of (client, model, label, sleep)
    worker_specs = []

    openai_keys = _get_openai_keys()
    for i, key in enumerate(openai_keys):
        raw = openai_lib.OpenAI(api_key=key, max_retries=3)
        client = instructor.from_openai(raw)
        worker_specs.append((client, os.environ.get("LLM_MODEL", "gpt-4o-mini"), f"oai-key{i+1}", openai_sleep))

    azure_client, azure_deployment = _get_azure_client()
    if azure_client is not None:
        worker_specs.append((azure_client, azure_deployment, "azure", 0.0))

    if not worker_specs:
        raise EnvironmentError("Set OPENAI_API_KEY (or OPENAI_API_KEY1/2/…) or AZURE_OPENAI_API_KEY in environment")

    n_openai = len(openai_keys)
    n_azure = 1 if azure_client is not None else 0
    console.print(
        f"[bold]Threads:[/bold] {n_openai} OpenAI (sleep={openai_sleep}s each) + {n_azure} Azure (no sleep)"
    )

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
        f"| already_done={stats.get('success', 0)} | to_process={len(to_process)} "
        f"| threads={len(worker_specs)}"
    )

    if not to_process:
        console.print("[green]All episodes already processed.[/green]")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ep_queue: queue.Queue = queue.Queue()
    for raw in to_process:
        ep_queue.put(raw)
    ep_queue.put(_SENTINEL)

    out_lock = threading.Lock()
    counter_lock = threading.Lock()
    counters = {"ok": 0, "fail": 0}

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
        task_id = progress.add_task("Enriching corpus", total=len(to_process))

        threads = []
        for client, model, label, sleep_s in worker_specs:
            t = threading.Thread(
                target=_worker,
                args=(
                    client, model, label, ep_queue, checkpointer,
                    out_lock, out_f, fail_f, SCHEMA_VERSION,
                    counters, counter_lock, progress, task_id, sleep_s,
                ),
                daemon=True,
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    with counter_lock:
        ok, fail = counters["ok"], counters["fail"]
    console.print(f"\n[bold green]Done.[/bold green] ok={ok} | fail={fail}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="data/processed/episodes.jsonl",          type=Path)
    parser.add_argument("--output", default="data/enriched/enriched_full_v5.jsonl",   type=Path)
    parser.add_argument("--failed", default="data/enriched/failed_full_v5.jsonl",     type=Path)
    parser.add_argument("--db",     default="data/enriched/checkpoint_full_v5.db",    type=Path)
    parser.add_argument("--limit",  default=None, type=int)
    parser.add_argument("--openai-sleep", default=3.0, type=float,
                        help="Seconds to sleep after each OpenAI request (throttles RPD)")
    args = parser.parse_args()
    run(args.input, args.output, args.failed, args.db, args.limit, args.openai_sleep)


if __name__ == "__main__":
    main()
