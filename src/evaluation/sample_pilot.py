"""
Sample a diverse pilot set for ontology validation before full labeling.

Usage:
    uv run python -m src.evaluation.sample_pilot             # 40-episode pilot
    uv run python -m src.evaluation.sample_pilot --full      # 150-episode full set
    uv run python -m src.evaluation.sample_pilot --n 30      # custom count
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

EPISODES_FILE = Path("data/processed/episodes.jsonl")
GOLDEN_DIR = Path("data/golden")

# Show → presumed vertical mapping (used for stratified sampling)
SHOW_VERTICAL: dict[str, str] = {
    "The Changelog: Software Development, Open Source": "technology",
    "Software Engineering Radio - The Podcast for Professional Software Developers": "technology",
    "Developer Tea": "technology",
    "Hanselminutes with Scott Hanselman": "technology",
    "Hard Fork": "technology",
    "Cognicast": "technology",
    "Software Engineering Daily": "technology",
    "Darknet Diaries": "true_crime",
    "StarTalk Radio": "science",
    "Radiolab": "science",
    "Science Vs": "science",
    "Brain Science with Ginger Campbell, MD: Neuroscience for Everyone": "science",
    "EconTalk": "business",
    "Masters of Scale": "business",
    "Pivot": "business",
    "Freakonomics Radio": "business",
    "The Ancients": "history",
    "American History Tellers": "history",
    "Dan Carlin's Hardcore History": "history",
    "Huberman Lab": "health",
    "The Art of Manliness": "health",
    "Conan O’Brien Needs A Friend": "comedy",
    "The Daily": "culture",
    "The Dan Bongino Show": "culture",
    "The Joe Rogan Experience": "culture",
    "The diet doctor": "health",
}

# Verticals to sample from, with target counts per vertical
PILOT_TARGETS: dict[str, int] = {
    "technology": 5,
    "science": 5,
    "business": 5,
    "history": 5,
    "true_crime": 3,
    "health": 5,
    "comedy": 4,
    "culture": 5,
}

FULL_TARGETS: dict[str, int] = {
    "technology": 22,
    "science": 22,
    "business": 22,
    "history": 18,
    "true_crime": 10,
    "health": 18,
    "comedy": 12,
    "culture": 26,
    # Total: 150
}


def load_episodes() -> list[dict]:
    episodes = []
    with open(EPISODES_FILE) as f:
        for line in f:
            episodes.append(json.loads(line))
    return episodes


def stratified_sample(episodes: list[dict], targets: dict[str, int], seed: int = 42) -> list[dict]:
    rng = random.Random(seed)

    by_vertical: dict[str, list[dict]] = defaultdict(list)
    unclassified: list[dict] = []

    for ep in episodes:
        vertical = SHOW_VERTICAL.get(ep["show_name"])
        if vertical:
            by_vertical[vertical].append(ep)
        else:
            unclassified.append(ep)

    sampled: list[dict] = []
    for vertical, n in targets.items():
        pool = by_vertical.get(vertical, [])
        # Prefer episodes with longer descriptions (more signal for labeling)
        pool_sorted = sorted(pool, key=lambda e: len(e.get("description", "")), reverse=True)
        # Sample from top 50% by description length to avoid very sparse episodes
        top_half = pool_sorted[: max(len(pool_sorted) // 2, n * 3)]
        chosen = rng.sample(top_half, min(n, len(top_half)))
        for ep in chosen:
            ep["_sampled_vertical"] = vertical
        sampled.extend(chosen)

    return sampled


def save_queue(episodes: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids: set[str] = set()
    if path.exists():
        with open(path) as f:
            for line in f:
                try:
                    existing_ids.add(json.loads(line)["episode_id"])
                except (json.JSONDecodeError, KeyError):
                    pass

    new_episodes = [ep for ep in episodes if ep["episode_id"] not in existing_ids]

    with open(path, "a") as f:
        for ep in new_episodes:
            f.write(json.dumps(ep, default=str) + "\n")

    print(f"Queue: {len(episodes)} episodes ({len(new_episodes)} new, {len(existing_ids)} already queued)")
    print(f"Saved to: {path}")

    # Print vertical distribution
    from collections import Counter
    dist = Counter(ep.get("_sampled_vertical", "unknown") for ep in episodes)
    print("\nVertical distribution:")
    for v, n in sorted(dist.items()):
        print(f"  {v:<25} {n}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Sample full 150-episode set")
    parser.add_argument("--n", type=int, help="Override total count")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    episodes = load_episodes()
    print(f"Loaded {len(episodes)} episodes from corpus")

    if args.full:
        targets = FULL_TARGETS
        queue_file = GOLDEN_DIR / "labeling_queue.jsonl"
        label = "full"
    else:
        targets = PILOT_TARGETS
        queue_file = GOLDEN_DIR / "pilot_queue.jsonl"
        label = "pilot"

    sampled = stratified_sample(episodes, targets, seed=args.seed)
    print(f"\nSampled {len(sampled)} episodes for {label} set")
    save_queue(sampled, queue_file)


if __name__ == "__main__":
    main()
