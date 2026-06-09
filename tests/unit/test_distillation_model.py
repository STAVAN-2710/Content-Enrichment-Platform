import pytest
import torch
from src.distillation.labels import LabelEncoders
from src.distillation.model import PodcastClassifier, LABEL_CONFIG

def test_forward_output_shapes():
    """Forward pass produces correct logit shapes for a batch of 2."""
    enc = LabelEncoders()
    model = PodcastClassifier("distilbert-base-uncased")
    model.eval()
    batch_size = 2
    seq_len = 32
    input_ids = torch.zeros(batch_size, seq_len, dtype=torch.long)
    attention_mask = torch.ones(batch_size, seq_len, dtype=torch.long)
    with torch.no_grad():
        logits = model(input_ids, attention_mask)
    assert set(logits.keys()) == {"mood", "difficulty", "format", "primary_topics", "secondary_topics", "best_listening_context"}
    assert logits["mood"].shape == (batch_size, enc.vocab_size("mood"))
    assert logits["difficulty"].shape == (batch_size, enc.vocab_size("difficulty"))
    assert logits["format"].shape == (batch_size, enc.vocab_size("format"))
    assert logits["primary_topics"].shape == (batch_size, enc.vocab_size("primary_topics"))
    assert logits["secondary_topics"].shape == (batch_size, enc.vocab_size("secondary_topics"))
    assert logits["best_listening_context"].shape == (batch_size, enc.vocab_size("best_listening_context"))

def test_label_config_completeness():
    from src.distillation.labels import ALL_FIELDS
    assert set(LABEL_CONFIG.keys()) == set(ALL_FIELDS)
