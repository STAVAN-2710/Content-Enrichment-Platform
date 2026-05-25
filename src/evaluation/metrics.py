"""
Per-attribute evaluation metrics for the enrichment evaluation framework.

Attribute types and their metrics:
  - Single-value categoricals (mood, difficulty, format):
      per-class precision/recall/F1, macro-averaged F1 via sklearn
  - Multi-value lists (primary_topics, best_listening_context):
      set-level precision@K and recall@K
  - Free-form text (summary_one_sentence):
      BERTScore F1 (semantic similarity)

Entity normalization is applied before scoring to prevent penalizing
semantically identical entities with different surface forms.
"""
import re
from dataclasses import dataclass, field
from typing import Any

from sklearn.metrics import classification_report, f1_score


# ---------------------------------------------------------------------------
# Entity normalization
# ---------------------------------------------------------------------------

_HONORIFICS = re.compile(
    r"\b(dr|prof|mr|mrs|ms|sir|rev|lt|gen|sgt|cpl|pvt|capt|col|maj)\.?\s+",
    re.IGNORECASE,
)


def normalize_entity(entity: str) -> str:
    """Lowercase, strip honorifics, collapse whitespace."""
    entity = entity.strip().lower()
    entity = _HONORIFICS.sub("", entity)
    entity = re.sub(r"\s+", " ", entity).strip()
    # Strip surrounding quotes (common artifact from label_tool)
    entity = entity.strip('"\'')
    return entity


def normalize_entities(entities: list[str]) -> set[str]:
    return {normalize_entity(e) for e in entities if e.strip()}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CategoricalMetrics:
    attribute: str
    macro_f1: float
    macro_precision: float
    macro_recall: float
    per_class: dict[str, dict[str, float]]   # class → {precision, recall, f1}
    n_samples: int
    dominant_failure: str = ""


@dataclass
class SetMetrics:
    attribute: str
    precision_at_k: float
    recall_at_k: float
    k: int
    n_samples: int


@dataclass
class BertScoreMetrics:
    attribute: str
    f1_mean: float
    f1_std: float
    n_samples: int


@dataclass
class EntityMetrics:
    attribute: str
    precision: float
    recall: float
    f1: float
    n_samples: int


@dataclass
class EvaluationResult:
    mood: CategoricalMetrics | None = None
    difficulty: CategoricalMetrics | None = None
    format: CategoricalMetrics | None = None
    primary_topics: SetMetrics | None = None
    best_listening_context: SetMetrics | None = None
    summary_bertscore: BertScoreMetrics | None = None
    key_entities: EntityMetrics | None = None
    # pipeline health
    out_of_ontology_rate: float = 0.0
    dead_letter_rate: float = 0.0
    avg_processing_ms: float = 0.0
    n_total: int = 0


# ---------------------------------------------------------------------------
# Categorical metrics (mood, difficulty, format)
# ---------------------------------------------------------------------------

def categorical_metrics(
    attribute: str,
    gold: list[str],
    pred: list[str],
) -> CategoricalMetrics:
    assert len(gold) == len(pred), f"Length mismatch: {len(gold)} vs {len(pred)}"

    report = classification_report(gold, pred, output_dict=True, zero_division=0)
    macro = report.get("macro avg", {})

    per_class: dict[str, dict[str, float]] = {}
    for key, val in report.items():
        if isinstance(val, dict) and key not in ("macro avg", "weighted avg", "accuracy"):
            per_class[key] = {
                "precision": round(val.get("precision", 0.0), 4),
                "recall":    round(val.get("recall",    0.0), 4),
                "f1":        round(val.get("f1-score",  0.0), 4),
                "support":   val.get("support", 0),
            }

    return CategoricalMetrics(
        attribute=attribute,
        macro_f1=round(macro.get("f1-score", 0.0), 4),
        macro_precision=round(macro.get("precision", 0.0), 4),
        macro_recall=round(macro.get("recall", 0.0), 4),
        per_class=per_class,
        n_samples=len(gold),
    )


# ---------------------------------------------------------------------------
# Set-level metrics (primary_topics, best_listening_context)
# ---------------------------------------------------------------------------

def set_metrics_at_k(
    attribute: str,
    gold: list[list[str]],
    pred: list[list[str]],
    k: int,
) -> SetMetrics:
    assert len(gold) == len(pred)

    precisions, recalls = [], []
    for g_set, p_set in zip(gold, pred):
        g = set(g_set)
        p = set(p_set[:k])
        if not p:
            precisions.append(0.0)
        else:
            precisions.append(len(g & p) / len(p))
        if not g:
            recalls.append(1.0)
        else:
            recalls.append(len(g & p) / len(g))

    return SetMetrics(
        attribute=attribute,
        precision_at_k=round(sum(precisions) / len(precisions), 4),
        recall_at_k=round(sum(recalls) / len(recalls), 4),
        k=k,
        n_samples=len(gold),
    )


# ---------------------------------------------------------------------------
# BERTScore (summary_one_sentence)
# ---------------------------------------------------------------------------

def bertscore_metrics(
    attribute: str,
    references: list[str],
    candidates: list[str],
) -> BertScoreMetrics:
    import bert_score

    _, _, f1_tensor = bert_score.score(
        candidates,
        references,
        lang="en",
        verbose=False,
    )
    f1 = f1_tensor.numpy()
    return BertScoreMetrics(
        attribute=attribute,
        f1_mean=round(float(f1.mean()), 4),
        f1_std=round(float(f1.std()), 4),
        n_samples=len(references),
    )


# ---------------------------------------------------------------------------
# Entity F1 (with normalization)
# ---------------------------------------------------------------------------

def entity_f1_metrics(
    attribute: str,
    gold: list[list[str]],
    pred: list[list[str]],
) -> EntityMetrics:
    assert len(gold) == len(pred)

    precisions, recalls = [], []
    for g_raw, p_raw in zip(gold, pred):
        g = normalize_entities(g_raw)
        p = normalize_entities(p_raw)
        if not p:
            precisions.append(0.0)
        else:
            precisions.append(len(g & p) / len(p))
        if not g:
            recalls.append(1.0)
        else:
            recalls.append(len(g & p) / len(g))

    p_mean = sum(precisions) / len(precisions)
    r_mean = sum(recalls)    / len(recalls)
    f1 = (2 * p_mean * r_mean / (p_mean + r_mean)) if (p_mean + r_mean) > 0 else 0.0

    return EntityMetrics(
        attribute=attribute,
        precision=round(p_mean, 4),
        recall=round(r_mean, 4),
        f1=round(f1, 4),
        n_samples=len(gold),
    )


# ---------------------------------------------------------------------------
# Top-level scorer
# ---------------------------------------------------------------------------

def compute_all_metrics(
    gold_records: list[dict],
    pred_records: list[dict],
    skip_bertscore: bool = False,
) -> EvaluationResult:
    """Compute all metrics given parallel lists of gold and predicted dicts."""
    assert len(gold_records) == len(pred_records), (
        f"Gold/pred length mismatch: {len(gold_records)} vs {len(pred_records)}"
    )

    result = EvaluationResult(n_total=len(gold_records))

    # --- Single-value categoricals ---
    for attr in ("mood", "difficulty", "format"):
        g = [r[attr] for r in gold_records]
        p = [r[attr] for r in pred_records]
        setattr(result, attr, categorical_metrics(attr, g, p))

    # --- Multi-value sets ---
    result.primary_topics = set_metrics_at_k(
        "primary_topics",
        gold=[r["primary_topics"] for r in gold_records],
        pred=[r["primary_topics"] for r in pred_records],
        k=3,
    )
    result.best_listening_context = set_metrics_at_k(
        "best_listening_context",
        gold=[r["best_listening_context"] for r in gold_records],
        pred=[r["best_listening_context"] for r in pred_records],
        k=4,
    )

    # --- BERTScore ---
    if not skip_bertscore:
        refs  = [r.get("summary_one_sentence", "") for r in gold_records]
        cands = [r.get("summary_one_sentence", "") for r in pred_records]
        if any(refs) and any(cands):
            result.summary_bertscore = bertscore_metrics("summary_one_sentence", refs, cands)

    # --- Entity F1 ---
    result.key_entities = entity_f1_metrics(
        "key_entities",
        gold=[r.get("key_entities", []) for r in gold_records],
        pred=[r.get("key_entities", []) for r in pred_records],
    )

    # --- Pipeline health ---
    from typing import get_args
    from src.schemas.enrichment import TopicLiteral
    vocab = frozenset(get_args(TopicLiteral))

    oo_count = 0
    for r in pred_records:
        topics = r.get("primary_topics", []) + r.get("secondary_topics", [])
        oo_count += sum(1 for t in topics if t not in vocab)

    total_topics = sum(
        len(r.get("primary_topics", [])) + len(r.get("secondary_topics", []))
        for r in pred_records
    )
    result.out_of_ontology_rate = round(oo_count / max(total_topics, 1), 4)

    ms_values = []
    for r in pred_records:
        notes = r.get("notes", "") or ""
        m = re.search(r"processing_ms=(\d+(?:\.\d+)?)", notes)
        if m:
            ms_values.append(float(m.group(1)))
    result.avg_processing_ms = round(sum(ms_values) / len(ms_values), 1) if ms_values else 0.0

    return result
