import pytest
import numpy as np
from src.distillation.labels import LabelEncoders

def test_single_label_round_trip():
    enc = LabelEncoders()
    idx = enc.encode_single("mood", "calm")
    assert enc.decode_single("mood", idx) == "calm"

def test_multi_label_round_trip():
    enc = LabelEncoders()
    binarized = enc.encode_multi("primary_topics", ["artificial_intelligence", "data_science"])
    assert binarized.shape == (enc.vocab_size("primary_topics"),)
    labels = enc.decode_multi("primary_topics", binarized)
    assert set(labels) == {"artificial_intelligence", "data_science"}

def test_vocab_sizes():
    enc = LabelEncoders()
    assert enc.vocab_size("mood") == 8
    assert enc.vocab_size("difficulty") == 3
    assert enc.vocab_size("format") == 6
    assert enc.vocab_size("best_listening_context") == 8
    assert enc.vocab_size("primary_topics") == 50
    assert enc.vocab_size("secondary_topics") == 50

def test_is_multi_label():
    enc = LabelEncoders()
    assert enc.is_multi("primary_topics") is True
    assert enc.is_multi("secondary_topics") is True
    assert enc.is_multi("best_listening_context") is True
    assert enc.is_multi("mood") is False
    assert enc.is_multi("difficulty") is False
    assert enc.is_multi("format") is False

def test_unknown_label_raises():
    enc = LabelEncoders()
    with pytest.raises(ValueError):
        enc.encode_single("mood", "nonexistent_mood")

def test_encode_multi_unknown_label_raises():
    enc = LabelEncoders()
    with pytest.raises(ValueError):
        enc.encode_multi("primary_topics", ["artificial_intelligence", "not_a_real_topic"])

def test_decode_multi_threshold():
    enc = LabelEncoders()
    # Values exactly at threshold should be included, below should not
    vec = enc.encode_multi("best_listening_context", ["commute", "workout"])
    # Default threshold 0.5: both active labels returned
    result = enc.decode_multi("best_listening_context", vec)
    assert set(result) == {"commute", "workout"}
    # Threshold 1.1: nothing passes → empty
    result_high = enc.decode_multi("best_listening_context", vec, threshold=1.1)
    assert result_high == []
