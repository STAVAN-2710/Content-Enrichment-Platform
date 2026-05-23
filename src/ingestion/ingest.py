"""CLI entrypoint: python -m src.ingestion.ingest"""
import logging
from dotenv import load_dotenv

load_dotenv()

from src.ingestion.feeds import ALL_FEEDS
from src.ingestion.runner import run_ingestion

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


if __name__ == "__main__":
    run_ingestion(ALL_FEEDS, fetch_transcripts=False)
