"""
Split golden.jsonl into three fixed, non-overlapping sets:
  - data/golden/pilot_set.jsonl     — v0 schema records (sanity check only)
  - data/golden/eval_set.jsonl      — 100 v1 records   (iterative evaluation)
  - data/golden/regression_set.jsonl — remaining v1    (SEALED: CI only, never eyeball)

Run once; outputs are committed and never regenerated.
"""
import json
import random
from pathlib import Path

GOLDEN_PATH = Path("data/golden/golden.jsonl")
PILOT_OUT   = Path("data/golden/pilot_set.jsonl")
EVAL_OUT    = Path("data/golden/eval_set.jsonl")
REGR_OUT    = Path("data/golden/regression_set.jsonl")

EVAL_SIZE   = 100
RANDOM_SEED = 42


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"  Wrote {len(records):>3} records → {path}")


def split() -> None:
    records = [json.loads(l) for l in GOLDEN_PATH.open()]
    print(f"Loaded {len(records)} records from {GOLDEN_PATH}")

    pilot = [r for r in records if r.get("schema_version", 1) == 0]
    v1    = [r for r in records if r.get("schema_version", 1) == 1]

    print(f"  v0 (pilot): {len(pilot)}  |  v1: {len(v1)}")

    if len(v1) < EVAL_SIZE:
        raise ValueError(f"Need {EVAL_SIZE} v1 records for eval set, only have {len(v1)}")

    rng = random.Random(RANDOM_SEED)
    shuffled = list(v1)
    rng.shuffle(shuffled)

    eval_set = shuffled[:EVAL_SIZE]
    regr_set = shuffled[EVAL_SIZE:]

    _write_jsonl(PILOT_OUT, pilot)
    _write_jsonl(EVAL_OUT,  eval_set)
    _write_jsonl(REGR_OUT,  regr_set)

    total_out = len(pilot) + len(eval_set) + len(regr_set)
    assert total_out == len(records), f"Record count mismatch: {total_out} != {len(records)}"
    print(f"\nSplit complete. Total: {total_out} (pilot={len(pilot)}, eval={len(eval_set)}, regression={len(regr_set)})")
    print("WARNING: regression_set.jsonl is now SEALED. Do not inspect or use it outside CI.")


if __name__ == "__main__":
    split()
