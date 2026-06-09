"""
Custom PyTorch training loop for PodcastClassifier.

Handles multi-task loss (CrossEntropy for single-label, BCE for multi-label),
AdamW optimiser with linear warmup, and returns best-epoch checkpoint.
"""
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from src.distillation.labels import LabelEncoders, SINGLE_LABEL_FIELDS, MULTI_LABEL_FIELDS
from src.distillation.model import PodcastClassifier

_enc = LabelEncoders()

MAX_LENGTH = 256


class EpisodeDataset(Dataset):
    def __init__(self, records: list[dict], tokenizer, max_length: int = MAX_LENGTH):
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        rec = self.records[idx]
        text = rec.get("text_for_enrichment", "")
        enc = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        item = {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
        }
        for field in SINGLE_LABEL_FIELDS:
            item[f"label_{field}"] = torch.tensor(_enc.encode_single(field, rec[field]), dtype=torch.long)
        for field in MULTI_LABEL_FIELDS:
            item[f"label_{field}"] = torch.tensor(_enc.encode_multi(field, rec[field]), dtype=torch.float32)
        return item


def _compute_loss(logits: dict, batch: dict, device: torch.device) -> torch.Tensor:
    loss = torch.tensor(0.0, device=device)
    for field in SINGLE_LABEL_FIELDS:
        targets = batch[f"label_{field}"].to(device)
        loss = loss + F.cross_entropy(logits[field], targets)
    for field in MULTI_LABEL_FIELDS:
        targets = batch[f"label_{field}"].to(device)
        loss = loss + F.binary_cross_entropy_with_logits(logits[field], targets)
    return loss


def train_one_run(
    model_name: str,
    train_records: list[dict],
    test_records: list[dict],
    output_dir: Path,
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 2e-5,
    warmup_ratio: float = 0.1,
    seed: int = 42,
) -> dict[str, float]:
    """Train model and return best test macro-F1 per field."""
    torch.manual_seed(seed)
    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"  device={device} | train={len(train_records)} | test={len(test_records)}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    train_ds = EpisodeDataset(train_records, tokenizer)
    test_ds = EpisodeDataset(test_records, tokenizer)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    model = PodcastClassifier(model_name).to(device)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    best_metrics: dict[str, float] = {}
    best_avg_f1 = -1.0

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = model(input_ids, attention_mask)
            loss = _compute_loss(logits, batch, device)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(train_loader)

        metrics = _evaluate(model, test_loader, device)
        avg_f1 = np.mean(list(metrics.values()))
        print(f"  epoch {epoch}/{epochs} | loss={avg_loss:.4f} | avg_f1={avg_f1:.4f}")

        if avg_f1 > best_avg_f1:
            best_avg_f1 = avg_f1
            best_metrics = metrics
            output_dir.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output_dir / "best_model.pt")

    return best_metrics


def _evaluate(model: PodcastClassifier, loader: DataLoader, device: torch.device) -> dict[str, float]:
    from sklearn.metrics import f1_score

    model.eval()
    preds: dict[str, list] = {f: [] for f in list(SINGLE_LABEL_FIELDS) + list(MULTI_LABEL_FIELDS)}
    golds: dict[str, list] = {f: [] for f in list(SINGLE_LABEL_FIELDS) + list(MULTI_LABEL_FIELDS)}

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = model(input_ids, attention_mask)

            for field in SINGLE_LABEL_FIELDS:
                pred_idx = logits[field].argmax(dim=-1).cpu().numpy()
                gold_idx = batch[f"label_{field}"].numpy()
                preds[field].extend(pred_idx.tolist())
                golds[field].extend(gold_idx.tolist())

            for field in MULTI_LABEL_FIELDS:
                pred_bin = (torch.sigmoid(logits[field]) > 0.5).cpu().numpy()
                gold_bin = batch[f"label_{field}"].numpy()
                preds[field].extend(pred_bin.tolist())
                golds[field].extend(gold_bin.tolist())

    metrics: dict[str, float] = {}
    for field in SINGLE_LABEL_FIELDS:
        metrics[field] = f1_score(golds[field], preds[field], average="macro", zero_division=0)
    for field in MULTI_LABEL_FIELDS:
        metrics[field] = f1_score(golds[field], preds[field], average="macro", zero_division=0)
    return metrics
