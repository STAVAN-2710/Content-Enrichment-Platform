import json
import logging
import os
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.ingestion.rss_fetcher import fetch_feeds
from src.ingestion.normalizer import normalize_episode, is_english
from src.schemas.episode import PodcastEpisode

logger = logging.getLogger(__name__)
console = Console()

PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", "data/processed"))
RAW_ERROR_LOG = Path(os.getenv("DATA_RAW_DIR", "data/raw")) / "ingestion_errors.log"
NON_ENGLISH_LOG = Path(os.getenv("DATA_RAW_DIR", "data/raw")) / "non_english.jsonl"


def _load_seen_ids(output_file: Path) -> set[str]:
    seen = set()
    if output_file.exists():
        with open(output_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    seen.add(data["episode_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return seen


def run_ingestion(
    feed_urls: list[str],
    output_filename: str = "episodes.jsonl",
    fetch_transcripts: bool = False,
) -> dict:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)

    output_file = PROCESSED_DIR / output_filename
    seen_ids = _load_seen_ids(output_file)

    stats = {
        "feeds_processed": 0,
        "episodes_written": 0,
        "episodes_skipped_duplicate": 0,
        "episodes_skipped_non_english": 0,
        "episodes_skipped_invalid": 0,
        "errors": 0,
    }

    with (
        open(output_file, "a") as out_f,
        open(NON_ENGLISH_LOG, "a") as non_en_f,
        open(RAW_ERROR_LOG, "a") as err_f,
        Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress,
    ):
        task = progress.add_task("Ingesting feeds...", total=len(feed_urls))

        for result in fetch_feeds(feed_urls, fetch_transcripts=fetch_transcripts):
            stats["feeds_processed"] += 1

            for error in result.errors:
                err_f.write(f"{result.feed_url}: {error}\n")
                stats["errors"] += 1

            for episode in result.episodes:
                if episode.episode_id in seen_ids:
                    stats["episodes_skipped_duplicate"] += 1
                    continue

                episode = normalize_episode(episode)

                if not is_english(episode):
                    non_en_f.write(episode.model_dump_json() + "\n")
                    stats["episodes_skipped_non_english"] += 1
                    seen_ids.add(episode.episode_id)
                    continue

                out_f.write(episode.model_dump_json() + "\n")
                seen_ids.add(episode.episode_id)
                stats["episodes_written"] += 1

            progress.advance(task)

    console.print(f"\n[bold green]Ingestion complete[/bold green]")
    console.print(f"  Written:          {stats['episodes_written']}")
    console.print(f"  Duplicates:       {stats['episodes_skipped_duplicate']}")
    console.print(f"  Non-English:      {stats['episodes_skipped_non_english']}")
    console.print(f"  Errors:           {stats['errors']}")
    console.print(f"  Output:           {output_file}")

    return stats


def load_episodes(filename: str = "episodes.jsonl") -> list[PodcastEpisode]:
    path = PROCESSED_DIR / filename
    episodes = []
    with open(path) as f:
        for line in f:
            episodes.append(PodcastEpisode.model_validate_json(line))
    return episodes
