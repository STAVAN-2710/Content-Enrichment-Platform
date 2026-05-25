"""
Evaluation report generator.

Matches golden eval set episodes with LLM enrichments, computes all metrics,
runs hallucination checks, and produces a markdown report committed to the repo.

CLI usage:
    uv run python -m src.evaluation.report \
        --golden data/golden/eval_set.jsonl \
        --enriched data/enriched/enriched.jsonl \
        --processed data/processed/episodes.jsonl \
        --output data/golden/eval_report_v1.md \
        [--skip-bertscore] [--skip-llm-judge]
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from src.evaluation.hallucination import batch_hallucination_check
from src.evaluation.metrics import (
    BertScoreMetrics,
    CategoricalMetrics,
    EvaluationResult,
    EntityMetrics,
    SetMetrics,
    compute_all_metrics,
)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open() if l.strip()]


def _index_by_id(records: list[dict]) -> dict[str, dict]:
    return {r["episode_id"]: r for r in records}


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _categorical_rows(m: CategoricalMetrics) -> list[str]:
    lines = [
        f"| **{m.attribute}** | {_fmt_pct(m.macro_precision)} | "
        f"{_fmt_pct(m.macro_recall)} | **{_fmt_pct(m.macro_f1)}** "
        f"| n={m.n_samples} |",
    ]
    for cls, vals in sorted(m.per_class.items()):
        lines.append(
            f"|   ↳ {cls} | {_fmt_pct(vals['precision'])} | "
            f"{_fmt_pct(vals['recall'])} | {_fmt_pct(vals['f1'])} "
            f"| support={int(vals['support'])} |"
        )
    return lines


def render_report(
    result: EvaluationResult,
    hallucination: dict,
    prompt_version: str,
    schema_version: int,
) -> str:
    lines = [
        "# Enrichment Evaluation Report",
        "",
        f"**Generated:** {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Prompt version:** {prompt_version}  ",
        f"**Schema version:** {schema_version}  ",
        f"**Eval episodes:** {result.n_total}",
        "",
        "---",
        "",
        "## Attribute Metrics",
        "",
        "| Attribute | Precision | Recall | F1 | Notes |",
        "|-----------|-----------|--------|----|-------|",
    ]

    for attr in ("mood", "difficulty", "format"):
        m: CategoricalMetrics | None = getattr(result, attr)
        if m:
            lines.extend(_categorical_rows(m))

    for attr in ("primary_topics", "best_listening_context"):
        m: SetMetrics | None = getattr(result, attr)
        if m:
            lines.append(
                f"| **{attr}** (P@{m.k} / R@{m.k}) | "
                f"{_fmt_pct(m.precision_at_k)} | "
                f"{_fmt_pct(m.recall_at_k)} | — | n={m.n_samples} |"
            )

    lines += [
        "",
        "## Free-Form Quality",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]

    bs: BertScoreMetrics | None = result.summary_bertscore
    if bs:
        lines.append(
            f"| BERTScore F1 (summary) | {_fmt_pct(bs.f1_mean)} ± {_fmt_pct(bs.f1_std)} |"
        )
    else:
        lines.append("| BERTScore F1 (summary) | *skipped* |")

    lines += [
        f"| LLM hallucination rate | {_fmt_pct(hallucination.get('overall_llm_hallucination_rate', 0))} "
        f"(n={hallucination.get('llm_judge_n', 0)}) |",
        f"| Entity hallucination rate | {_fmt_pct(hallucination.get('overall_entity_hallucination_rate', 0))} "
        f"(n={hallucination.get('entity_check_n', 0)}) |",
    ]

    em: EntityMetrics | None = result.key_entities
    if em:
        lines.append(
            f"| Entity F1 (key_entities) | {_fmt_pct(em.f1)} "
            f"(P={_fmt_pct(em.precision)} R={_fmt_pct(em.recall)}) |"
        )

    lines += [
        "",
        "## Pipeline Health",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Out-of-ontology topic rate | {_fmt_pct(result.out_of_ontology_rate)} |",
        f"| Dead letter rate | {_fmt_pct(result.dead_letter_rate)} |",
        f"| Avg processing time | {result.avg_processing_ms:.0f} ms/episode |",
    ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main evaluation runner
# ---------------------------------------------------------------------------

def run_evaluation(
    golden_path: Path,
    enriched_path: Path,
    processed_path: Path,
    output_path: Path,
    skip_bertscore: bool = False,
    skip_llm_judge: bool = False,
) -> EvaluationResult:
    golden_records  = _load_jsonl(golden_path)
    enriched_records = _load_jsonl(enriched_path)
    processed_records = _load_jsonl(processed_path) if processed_path.exists() else []

    enriched_idx  = _index_by_id(enriched_records)
    processed_idx = _index_by_id(processed_records)

    # Match golden to enriched — only evaluate episodes where both exist
    matched_gold, matched_pred = [], []
    missing = []

    for g in golden_records:
        eid = g["episode_id"]
        if eid in enriched_idx:
            matched_gold.append(g)
            matched_pred.append(enriched_idx[eid])
        else:
            missing.append(eid)

    if missing:
        print(f"[warn] {len(missing)} golden episodes have no enrichment — skipped from metrics")

    print(f"Evaluating {len(matched_gold)} matched episodes...")

    # Compute metrics
    result = compute_all_metrics(matched_gold, matched_pred, skip_bertscore=skip_bertscore)

    # Dead letter rate relative to all golden episodes attempted
    total_attempted = len(golden_records)
    result.dead_letter_rate = round(len(missing) / max(total_attempted, 1), 4)
    result.n_total = len(matched_gold)

    # Build source text map for hallucination checks
    source_texts: dict[str, str] = {}
    for ep in processed_records:
        from src.schemas.episode import PodcastEpisode
        try:
            episode = PodcastEpisode.model_validate(ep)
            source_texts[episode.episode_id] = episode.text_for_enrichment
        except Exception:
            pass

    hallucination = batch_hallucination_check(
        matched_pred,
        source_texts=source_texts,
        run_llm_judge=not skip_llm_judge,
    )

    # Infer prompt/schema version from first pred record
    prompt_version  = matched_pred[0].get("prompt_version",  "unknown") if matched_pred else "unknown"
    schema_version  = matched_pred[0].get("schema_version",  0)         if matched_pred else 0

    report_md = render_report(result, hallucination, prompt_version, schema_version)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md)
    print(f"Report written to {output_path}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate enrichment evaluation report")
    parser.add_argument("--golden",    required=True,  type=Path)
    parser.add_argument("--enriched",  required=True,  type=Path)
    parser.add_argument("--processed", default=Path("data/processed/episodes.jsonl"), type=Path)
    parser.add_argument("--output",    default=Path("data/golden/eval_report_v1.md"), type=Path)
    parser.add_argument("--skip-bertscore",  action="store_true")
    parser.add_argument("--skip-llm-judge",  action="store_true")
    args = parser.parse_args()

    run_evaluation(
        golden_path=args.golden,
        enriched_path=args.enriched,
        processed_path=args.processed,
        output_path=args.output,
        skip_bertscore=args.skip_bertscore,
        skip_llm_judge=args.skip_llm_judge,
    )


if __name__ == "__main__":
    main()
