import json
import tempfile
from pathlib import Path
import pytest
from src.distillation.dataset import build_splits, load_high_conf_records, sample_train

def _write_jsonl(path, records):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

def _make_enrichment(episode_id, topic_conf=0.85):
    return {
        "episode_id": episode_id,
        "mood": "neutral",
        "best_listening_context": ["commute", "learning"],
        "primary_topics": ["artificial_intelligence"],
        "secondary_topics": ["data_science"],
        "difficulty": "intermediate",
        "format": "interview",
        "confidence_scores": {
            "mood": 0.9, "difficulty": 0.9, "primary_topics": topic_conf,
            "format": 0.9, "best_listening_context": 0.9,
        },
    }

def _make_episode(episode_id):
    return {"episode_id": episode_id, "text_for_enrichment": f"Title: Ep {episode_id}\nDescription: about AI"}

def test_load_high_conf_filters_low():
    with tempfile.TemporaryDirectory() as d:
        ep_path = Path(d) / "episodes.jsonl"
        en_path = Path(d) / "enriched.jsonl"
        _write_jsonl(ep_path, [_make_episode(str(i)) for i in range(10)])
        records = [_make_enrichment(str(i), topic_conf=(0.8 if i < 8 else 0.5)) for i in range(10)]
        _write_jsonl(en_path, records)
        result = load_high_conf_records(en_path, ep_path, min_topic_conf=0.70)
        assert len(result) == 8

def test_build_splits_sizes():
    with tempfile.TemporaryDirectory() as d:
        ep_path = Path(d) / "episodes.jsonl"
        en_path = Path(d) / "enriched.jsonl"
        _write_jsonl(ep_path, [_make_episode(str(i)) for i in range(700)])
        _write_jsonl(en_path, [_make_enrichment(str(i)) for i in range(700)])
        records = load_high_conf_records(en_path, ep_path)
        test_set, train_pool = build_splits(records, test_size=500, seed=42)
        assert len(test_set) == 500
        assert len(train_pool) == 200
        # No overlap
        test_ids = {r["episode_id"] for r in test_set}
        train_ids = {r["episode_id"] for r in train_pool}
        assert test_ids.isdisjoint(train_ids)

def test_record_has_text():
    with tempfile.TemporaryDirectory() as d:
        ep_path = Path(d) / "episodes.jsonl"
        en_path = Path(d) / "enriched.jsonl"
        _write_jsonl(ep_path, [_make_episode("ep1")])
        _write_jsonl(en_path, [_make_enrichment("ep1")])
        records = load_high_conf_records(en_path, ep_path)
        assert "text_for_enrichment" in records[0]
        assert records[0]["text_for_enrichment"] == "Title: Ep ep1\nDescription: about AI"

def test_sample_train_deterministic():
    pool = [{"episode_id": str(i)} for i in range(100)]
    s1 = sample_train(pool, 20, seed=42)
    s2 = sample_train(pool, 20, seed=42)
    assert [r["episode_id"] for r in s1] == [r["episode_id"] for r in s2]

def test_sample_train_raises_if_too_large():
    pool = [{"episode_id": str(i)} for i in range(5)]
    with pytest.raises(ValueError):
        sample_train(pool, 10)
