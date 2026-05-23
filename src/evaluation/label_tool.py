"""
Interactive CLI labeling tool for the podcast golden dataset.

Usage:
    uv run python -m src.evaluation.label_tool                   # label pilot queue
    uv run python -m src.evaluation.label_tool --queue full      # label full queue
    uv run python -m src.evaluation.label_tool --review          # review your labels so far
    uv run python -m src.evaluation.label_tool --stats           # show progress stats

Controls while labeling:
    Enter number(s) for choices    e.g.  1  or  1,3  or  1 3
    s                              skip this episode (come back later)
    q                              quit and save progress
    ?                              show field guidelines reminder
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from src.schemas.enrichment import (
    EpisodeEnrichment,
    MoodLiteral,
    ListeningContextLiteral,
    TopicLiteral,
    DifficultyLiteral,
    FormatLiteral,
    EnrichmentQualityLiteral,
    LabelerConfidenceLiteral,
)

GOLDEN_DIR = Path("data/golden")
PILOT_QUEUE = GOLDEN_DIR / "pilot_queue.jsonl"
FULL_QUEUE = GOLDEN_DIR / "labeling_queue.jsonl"
GOLDEN_FILE = GOLDEN_DIR / "golden.jsonl"
GUIDELINES_FILE = GOLDEN_DIR / "LABELING_GUIDELINES.md"

console = Console()

# ---------------------------------------------------------------------------
# Vocab lists (same order as Literal definitions — used for menu display)
# ---------------------------------------------------------------------------

MOODS = ["energetic", "calm", "intense", "melancholic", "humorous", "serious", "inspirational", "neutral"]
CONTEXTS = ["commute", "workout", "deep_work", "casual_listening", "cooking", "sleep", "social", "learning"]
TOPICS = [
    "artificial_intelligence", "software_engineering", "cybersecurity", "hardware", "startups_and_vc", "data_science",
    "neuroscience", "physics", "biology", "medicine", "astronomy", "climate_and_environment",
    "entrepreneurship", "investing", "marketing", "leadership", "economics", "productivity",
    "ancient_history", "modern_history", "military_history", "political_history", "cultural_history",
    "cybercrime", "true_crime",
    "nutrition", "fitness", "mental_health", "sleep", "longevity",
    "ethics", "philosophy_of_mind", "spirituality",
    "comedy", "satire",
    "relationships", "personal_finance", "career", "habits_and_mindset",
    "politics", "media_and_journalism", "social_issues", "sports", "arts_and_entertainment",
]
DIFFICULTIES = ["beginner", "intermediate", "advanced"]
FORMATS = ["interview", "solo_monologue", "panel_discussion", "narrative_storytelling", "debate", "educational_lecture"]
QUALITIES = ["high", "medium", "low"]
CONFIDENCES = ["high", "medium", "low"]

TOPIC_GROUPS = {
    "Technology":        TOPICS[0:6],
    "Science":           TOPICS[6:12],
    "Business":          TOPICS[12:18],
    "History":           TOPICS[18:23],
    "True Crime":        TOPICS[23:25],
    "Health":            TOPICS[25:30],
    "Philosophy":        TOPICS[30:33],
    "Comedy":            TOPICS[33:35],
    "Personal Dev":      TOPICS[35:39],
    "Culture":           TOPICS[39:],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_labeled_ids() -> set[str]:
    return {r["episode_id"] for r in _load_jsonl(GOLDEN_FILE)}


def _load_queue(queue_file: Path) -> list[dict]:
    return _load_jsonl(queue_file)


def _save_label(record: dict) -> None:
    GOLDEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOLDEN_FILE, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _numbered_menu(title: str, options: list[str], multi: bool = False, required: bool = True) -> list[str] | str:
    console.print(f"\n[bold cyan]{title}[/bold cyan]", end=" ")
    if multi:
        console.print("[dim](enter numbers separated by space or comma)[/dim]")
    else:
        console.print("[dim](enter one number)[/dim]")

    for i, opt in enumerate(options, 1):
        console.print(f"  [dim]{i:2}[/dim]  {opt}")

    while True:
        try:
            raw = console.input("[green]> [/green]").strip()
        except EOFError:
            return [] if multi else ""

        if raw.lower() == "q":
            raise KeyboardInterrupt
        if raw.lower() == "s":
            raise SkipEpisode
        if raw.lower() == "?":
            _show_guidelines_hint()
            continue
        if not raw and not required:
            return [] if multi else ""

        try:
            indices = [int(x.strip()) for x in raw.replace(",", " ").split() if x.strip()]
            chosen = [options[i - 1] for i in indices if 1 <= i <= len(options)]
            if chosen or not required:
                return chosen if multi else (chosen[0] if chosen else "")
        except (ValueError, IndexError):
            pass

        console.print("[red]  Invalid choice — try again[/red]")


def _topic_menu(title: str, multi: bool, max_count: int, exclude: list[str] | None = None) -> list[str]:
    exclude = exclude or []
    console.print(f"\n[bold cyan]{title}[/bold cyan] [dim](max {max_count}, by group)[/dim]")

    flat_options: list[str] = []
    for group, topics in TOPIC_GROUPS.items():
        available = [t for t in topics if t not in exclude]
        if not available:
            continue
        console.print(f"  [bold yellow]{group}[/bold yellow]")
        for t in available:
            flat_options.append(t)
            console.print(f"    [dim]{len(flat_options):2}[/dim]  {t}")

    while True:
        try:
            raw = console.input("[green]> [/green]").strip()
        except EOFError:
            return []

        if raw.lower() == "q":
            raise KeyboardInterrupt
        if raw.lower() == "s":
            raise SkipEpisode
        if raw.lower() == "?":
            _show_guidelines_hint()
            continue
        if not raw and not multi:
            console.print("[red]  Required — pick at least one[/red]")
            continue
        if not raw and multi:
            return []

        try:
            indices = [int(x.strip()) for x in raw.replace(",", " ").split() if x.strip()]
            chosen = [flat_options[i - 1] for i in indices if 1 <= i <= len(flat_options)]
            if chosen and len(chosen) <= max_count:
                return chosen
            if not chosen and not multi:
                console.print("[red]  Pick at least one[/red]")
                continue
            if len(chosen) > max_count:
                console.print(f"[red]  Max {max_count} — pick fewer[/red]")
                continue
        except (ValueError, IndexError):
            pass

        console.print("[red]  Invalid — try again[/red]")


def _show_guidelines_hint() -> None:
    if GUIDELINES_FILE.exists():
        console.print(f"\n[dim]Guidelines: {GUIDELINES_FILE}[/dim]")
        console.print("[dim]Open it in another terminal for reference.[/dim]\n")
    else:
        console.print("[yellow]No guidelines file found yet.[/yellow]\n")


def _display_episode(ep: dict, idx: int, total: int) -> None:
    progress = f"Episode {idx}/{total}"
    vertical = ep.get("_sampled_vertical", "?")
    header = f"{progress}  ·  {ep['show_name']}  ·  [{vertical}]"

    description = ep.get("description", "").strip()
    if len(description) > 1200:
        description = description[:1200] + "…"

    text = Text()
    text.append(ep["title"] + "\n\n", style="bold white")
    text.append(description, style="white")

    console.print()
    console.print(Panel(text, title=header, border_style="blue", padding=(1, 2)))


class SkipEpisode(Exception):
    pass


# ---------------------------------------------------------------------------
# Labeling flow
# ---------------------------------------------------------------------------

def label_episode(ep: dict) -> dict:
    """Prompt the labeler for all fields. Returns a dict ready to save."""

    # Mood
    mood = _numbered_menu("MOOD", MOODS, multi=False)

    # Listening context
    contexts = _numbered_menu("BEST LISTENING CONTEXT (1-4)", CONTEXTS, multi=True)
    while not contexts:
        console.print("[red]  Pick at least one[/red]")
        contexts = _numbered_menu("BEST LISTENING CONTEXT (1-4)", CONTEXTS, multi=True)

    # Primary topics
    primary = _topic_menu("PRIMARY TOPICS (1-3)", multi=True, max_count=3)

    # Secondary topics (optional)
    secondary = _topic_menu("SECONDARY TOPICS (0-5, optional — press Enter to skip)", multi=True, max_count=5, exclude=primary)

    # Difficulty
    difficulty = _numbered_menu("DIFFICULTY", DIFFICULTIES, multi=False)

    # Format
    fmt = _numbered_menu("FORMAT", FORMATS, multi=False)

    # Summary
    console.print("\n[bold cyan]SUMMARY (one sentence, max 200 chars)[/bold cyan] [dim]grounded in what you read[/dim]")
    while True:
        try:
            summary = console.input("[green]> [/green]").strip()
        except EOFError:
            summary = ""
        if summary.lower() == "q":
            raise KeyboardInterrupt
        if summary.lower() == "s":
            raise SkipEpisode
        if summary and len(summary) <= 200:
            break
        if not summary:
            console.print("[red]  Required[/red]")
        elif len(summary) > 200:
            console.print(f"[red]  Too long ({len(summary)} chars) — shorten it[/red]")

    # Key entities
    console.print("\n[bold cyan]KEY ENTITIES[/bold cyan] [dim](comma-separated people/companies/books/places — press Enter to skip)[/dim]")
    try:
        raw_entities = console.input("[green]> [/green]").strip()
    except EOFError:
        raw_entities = ""
    if raw_entities.lower() in ("q",):
        raise KeyboardInterrupt
    if raw_entities.lower() == "s":
        raise SkipEpisode
    entities = [e.strip() for e in raw_entities.split(",") if e.strip()][:10]

    # Content warnings
    console.print("\n[bold cyan]CONTENT WARNINGS[/bold cyan] [dim](comma-separated or Enter for none)[/dim]")
    try:
        raw_cw = console.input("[green]> [/green]").strip()
    except EOFError:
        raw_cw = ""
    if raw_cw.lower() == "q":
        raise KeyboardInterrupt
    if raw_cw.lower() == "s":
        raise SkipEpisode
    warnings = [w.strip() for w in raw_cw.split(",") if w.strip()]

    # Sponsored
    console.print("\n[bold cyan]IS SPONSORED?[/bold cyan] [dim](y/n — only if explicitly mentioned in description)[/dim]")
    while True:
        try:
            sp = console.input("[green]> [/green]").strip().lower()
        except EOFError:
            sp = "n"
        if sp == "q":
            raise KeyboardInterrupt
        if sp == "s":
            raise SkipEpisode
        if sp in ("y", "n", "yes", "no"):
            is_sponsored = sp in ("y", "yes")
            break
        console.print("[red]  Enter y or n[/red]")

    # Enrichment quality
    console.print("\n[bold cyan]ENRICHMENT QUALITY[/bold cyan] [dim](high=had good description, medium=sparse, low=almost no signal)[/dim]")
    quality = _numbered_menu("", QUALITIES, multi=False)

    # Labeler confidence
    confidence = _numbered_menu("YOUR CONFIDENCE IN THESE LABELS", CONFIDENCES, multi=False)

    # Notes (optional)
    console.print("\n[bold cyan]NOTES[/bold cyan] [dim](anything uncertain — press Enter to skip)[/dim]")
    try:
        notes = console.input("[green]> [/green]").strip() or None
    except EOFError:
        notes = None

    return {
        "episode_id": ep["episode_id"],
        "show_name": ep["show_name"],
        "title": ep["title"],
        "mood": mood,
        "best_listening_context": contexts,
        "primary_topics": primary,
        "secondary_topics": secondary,
        "difficulty": difficulty,
        "format": fmt,
        "summary_one_sentence": summary,
        "key_entities": entities,
        "content_warnings": warnings,
        "is_sponsored": is_sponsored,
        "enrichment_quality": quality,
        "confidence_scores": {},
        "labeler": "human",
        "labeler_confidence": confidence,
        "notes": notes,
        "labeled_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 0,
        "_sampled_vertical": ep.get("_sampled_vertical", "unknown"),
    }


# ---------------------------------------------------------------------------
# Review and stats
# ---------------------------------------------------------------------------

def show_stats() -> None:
    labels = _load_jsonl(GOLDEN_FILE)
    pilot = _load_jsonl(PILOT_QUEUE)
    full = _load_jsonl(FULL_QUEUE)

    labeled_ids = {r["episode_id"] for r in labels}

    console.print(f"\n[bold]Golden dataset stats[/bold]")
    console.print(f"  Labeled:      {len(labels)}")
    console.print(f"  Pilot queue:  {len(pilot)}  ({len(labeled_ids & {e['episode_id'] for e in pilot})} done)")
    if full:
        console.print(f"  Full queue:   {len(full)}  ({len(labeled_ids & {e['episode_id'] for e in full})} done)")

    if not labels:
        return

    from collections import Counter
    mood_dist = Counter(r["mood"] for r in labels)
    diff_dist = Counter(r["difficulty"] for r in labels)
    fmt_dist = Counter(r["format"] for r in labels)
    vert_dist = Counter(r.get("_sampled_vertical", "unknown") for r in labels)

    table = Table(box=box.SIMPLE)
    table.add_column("Field")
    table.add_column("Distribution")
    for field, dist in [("mood", mood_dist), ("difficulty", diff_dist), ("format", fmt_dist), ("vertical", vert_dist)]:
        table.add_row(field, "  ".join(f"{k}:{v}" for k, v in sorted(dist.items(), key=lambda x: -x[1])))
    console.print(table)


def show_review(n: int = 10) -> None:
    labels = _load_jsonl(GOLDEN_FILE)
    if not labels:
        console.print("No labels yet.")
        return
    console.print(f"\n[bold]Last {n} labels[/bold]")
    for r in labels[-n:]:
        console.print(f"  [cyan]{r['episode_id'][:8]}[/cyan]  {r.get('show_name', '')[:35]:<35}  mood={r['mood']:<12}  diff={r['difficulty']:<12}  {r['primary_topics']}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_labeling(queue_file: Path) -> None:
    queue = _load_queue(queue_file)
    if not queue:
        console.print(f"[yellow]Queue file not found or empty: {queue_file}[/yellow]")
        console.print("Run first:  uv run python -m src.evaluation.sample_pilot")
        return

    labeled_ids = _load_labeled_ids()
    remaining = [ep for ep in queue if ep["episode_id"] not in labeled_ids]

    if not remaining:
        console.print("[green]All episodes in this queue are labeled![/green]")
        show_stats()
        return

    console.print(f"\n[bold green]Starting labeling session[/bold green]")
    console.print(f"  Queue: {len(queue)} episodes  ·  Done: {len(labeled_ids)}  ·  Remaining: {len(remaining)}")
    console.print(f"  Controls: [cyan]s[/cyan]=skip  [cyan]q[/cyan]=quit  [cyan]?[/cyan]=guidelines hint\n")

    session_count = 0
    for idx, ep in enumerate(remaining, start=len(labeled_ids) + 1):
        _display_episode(ep, idx, len(queue))
        try:
            record = label_episode(ep)
        except SkipEpisode:
            console.print("[yellow]  → Skipped[/yellow]")
            continue
        except KeyboardInterrupt:
            console.print(f"\n[yellow]Session ended. Labeled {session_count} this session.[/yellow]")
            break

        _save_label(record)
        session_count += 1
        console.print(f"[green]  ✓ Saved[/green]")

    console.print(f"\n[bold]Session complete: {session_count} labeled this session[/bold]")
    show_stats()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Podcast episode labeling tool")
    parser.add_argument("--queue", choices=["pilot", "full"], default="pilot")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return
    if args.review:
        show_review()
        return

    queue_file = PILOT_QUEUE if args.queue == "pilot" else FULL_QUEUE
    run_labeling(queue_file)


if __name__ == "__main__":
    main()
