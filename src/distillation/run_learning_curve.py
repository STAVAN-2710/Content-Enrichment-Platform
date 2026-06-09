"""
Run learning curve experiments: 4 train sizes × 2 models.

CLI:
    PYTHONPATH=. python src/distillation/run_learning_curve.py \
        [--enriched data/enriched/enriched_full_v5.jsonl] \
        [--episodes data/processed/episodes.jsonl] \
        [--output   data/distillation/results.json] \
        [--models   deberta distilbert] \
        [--sizes    150 300 600 900]
"""
import argparse
import json
from pathlib import Path

from src.distillation.dataset import build_splits, load_high_conf_records, sample_train
from src.distillation.evaluate import print_learning_curve_table, save_results
from src.distillation.train import train_one_run

MODEL_NAMES = {
    "deberta": "microsoft/deberta-v3-small",
    "distilbert": "distilbert-base-uncased",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enriched", default="data/enriched/enriched_full_v5.jsonl", type=Path)
    parser.add_argument("--episodes", default="data/processed/episodes.jsonl", type=Path)
    parser.add_argument("--output",   default="data/distillation/results.json", type=Path)
    parser.add_argument("--models",   nargs="+", default=["deberta", "distilbert"])
    parser.add_argument("--sizes",    nargs="+", type=int, default=[150, 300, 600, 900])
    parser.add_argument("--epochs",   type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    print("Loading and filtering records…")
    records = load_high_conf_records(args.enriched, args.episodes, min_topic_conf=0.70)
    print(f"High-confidence records: {len(records)}")

    test_set, train_pool = build_splits(records, test_size=500, seed=42)
    print(f"Test set: {len(test_set)} | Train pool: {len(train_pool)}")

    # Load existing results if any (allows resuming interrupted runs)
    results: dict = {}
    if args.output.exists():
        with open(args.output) as f:
            results = json.load(f)
        print(f"Loaded existing results from {args.output}")

    for model_key in args.models:
        model_name = MODEL_NAMES[model_key]
        results.setdefault(model_key, {})
        for size in args.sizes:
            run_key = str(size)
            if run_key in results[model_key]:
                print(f"  Skipping {model_key} size={size} (already done)")
                continue
            print(f"\n=== {model_key} | train_size={size} ===")
            train_subset = sample_train(train_pool, size, seed=42)
            output_dir = args.output.parent / "checkpoints" / model_key / str(size)
            metrics = train_one_run(
                model_name=model_name,
                train_records=train_subset,
                test_records=test_set,
                output_dir=output_dir,
                epochs=args.epochs,
                batch_size=args.batch_size,
            )
            results[model_key][run_key] = metrics
            save_results(results, args.output)

    print("\n\n=== LEARNING CURVE RESULTS ===")
    print_learning_curve_table(results)
    save_results(results, args.output)


if __name__ == "__main__":
    main()
