import json
import random
from pathlib import Path


def load_high_conf_records(
    enriched_path: Path,
    episodes_path: Path,
    min_topic_conf: float = 0.70,
) -> list[dict]:
    """Join enrichments with episode text, filter by topic confidence."""
    text_lookup: dict[str, str] = {}
    with open(episodes_path) as f:
        for line in f:
            if line.strip():
                ep = json.loads(line)
                text_lookup[ep["episode_id"]] = ep.get("text_for_enrichment", "")

    records = []
    with open(enriched_path) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            conf = rec.get("confidence_scores", {}).get("primary_topics", 0.0)
            if conf < min_topic_conf:
                continue
            ep_id = rec["episode_id"]
            if ep_id not in text_lookup:
                continue
            rec["text_for_enrichment"] = text_lookup[ep_id]
            records.append(rec)
    return records


def build_splits(
    records: list[dict],
    test_size: int = 500,
    seed: int = 42,
) -> tuple[list[dict], list[dict]]:
    """Return (test_set, train_pool). test_set is fixed; train_pool is the remainder."""
    rng = random.Random(seed)
    shuffled = records.copy()
    rng.shuffle(shuffled)
    if len(shuffled) < test_size:
        raise ValueError(f"Not enough records ({len(shuffled)}) for test_size={test_size}")
    return shuffled[:test_size], shuffled[test_size:]


def sample_train(train_pool: list[dict], n: int, seed: int = 42) -> list[dict]:
    """Sample n records from train_pool (deterministic)."""
    if n > len(train_pool):
        raise ValueError(f"Requested {n} but pool only has {len(train_pool)}")
    rng = random.Random(seed)
    pool = train_pool.copy()
    rng.shuffle(pool)
    return pool[:n]
