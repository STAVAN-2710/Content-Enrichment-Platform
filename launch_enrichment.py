"""
Launcher: 1 OpenAI thread, throttled to ~9K req/day.

All keys share the same org RPD quota (10K/day). Running 1 thread with 3s sleep
keeps consumption safely under the limit. Increase openai_sleep to be more
conservative, decrease to go faster (risk 429s).

To swap which key is active, change ACTIVE_KEY below.
"""
import os

# Pick exactly ONE key to use — all are in the same org, more threads = faster burn
ACTIVE_KEY = "OPENAI_API_KEY1"

# Load .env values manually so we can selectively expose keys
from dotenv import dotenv_values
env = dotenv_values(".env")

# Blank Azure to prevent interference
os.environ["AZURE_OPENAI_API_KEY"] = ""

# Expose only the chosen key as OPENAI_API_KEY (what _get_openai_keys reads last)
# Blank the numbered slots to avoid picking up extras
for slot in ["OPENAI_API_KEY", "OPENAI_API_KEY1", "OPENAI_API_KEY2", "OPENAI_API_KEY3",
             "OPENAI_API_KEY4", "OPENAI_API_KEY5", "OPENAI_API_KEY6",
             "OPENAI_API_KEY7", "OPENAI_API_KEY8"]:
    os.environ[slot] = ""

os.environ[ACTIVE_KEY] = env.get(ACTIVE_KEY) or ""

from pathlib import Path
from src.pipeline.run_parallel_enrichment import run

run(
    input_path=Path("data/processed/episodes.jsonl"),
    output_path=Path("data/enriched/enriched_full_v5.jsonl"),
    failed_path=Path("data/enriched/failed_full_v5.jsonl"),
    db_path=Path("data/enriched/checkpoint_full_v5.db"),
    openai_sleep=3.0,
)
