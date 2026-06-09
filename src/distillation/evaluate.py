"""
Generate learning curve comparison table from experiment results.

Results format (JSON):
{
  "deberta": {
    "150": {"mood": 0.72, "difficulty": 0.61, ...},
    "300": {...},
    ...
  },
  "distilbert": { ... }
}
"""
import json
from pathlib import Path

FIELDS = ["mood", "difficulty", "format", "primary_topics", "secondary_topics", "best_listening_context"]
MODELS = {"deberta": "DeBERTa-v3-small", "distilbert": "DistilBERT"}
TRAIN_SIZES = [150, 300, 600, 900]


def load_results(results_path: Path) -> dict:
    with open(results_path) as f:
        return json.load(f)


def print_learning_curve_table(results: dict) -> None:
    header = f"{'Model':<20} {'Train':>6} | " + " | ".join(f"{f[:8]:>8}" for f in FIELDS) + " | {'Avg F1':>7}"
    print(header)
    print("-" * len(header))
    for model_key, model_label in MODELS.items():
        for size in TRAIN_SIZES:
            row = results.get(model_key, {}).get(str(size))
            if row is None:
                continue
            f1s = [row.get(f, 0.0) for f in FIELDS]
            avg = sum(f1s) / len(f1s)
            cols = " | ".join(f"{v:8.3f}" for v in f1s)
            print(f"{model_label:<20} {size:>6} | {cols} | {avg:7.3f}")


def save_results(results: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")
