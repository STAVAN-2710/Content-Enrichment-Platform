import time
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from src.schemas.episode import PodcastEpisode

logger = logging.getLogger(__name__)

FETCH_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT = 15


@dataclass
class FeedResult:
    feed_url: str
    episodes: list[PodcastEpisode]
    errors: list[str]


def _parse_duration(entry: feedparser.FeedParserDict) -> Optional[int]:
    duration = entry.get("itunes_duration")
    if not duration:
        return None
    try:
        parts = str(duration).split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0])
    except (ValueError, IndexError):
        return None


def _parse_published_date(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    try:
        t = entry.get("published_parsed") or entry.get("updated_parsed")
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def _extract_audio_url(entry: feedparser.FeedParserDict) -> Optional[str]:
    for link in entry.get("links", []):
        if link.get("type", "").startswith("audio/"):
            return link.get("href")
    enclosures = entry.get("enclosures", [])
    if enclosures:
        return enclosures[0].get("href")
    return None


def _extract_transcript_url(description: str) -> Optional[str]:
    """Look for transcript links in episode show notes."""
    soup = BeautifulSoup(description, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = a.get_text().lower()
        if "transcript" in href or "transcript" in text:
            return a["href"]
    return None


def _fetch_transcript(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove nav/header/footer noise
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:20000] if len(text) > 500 else None
    except Exception:
        return None


def _clean_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def fetch_feed(feed_url: str, fetch_transcripts: bool = False) -> FeedResult:
    episodes: list[PodcastEpisode] = []
    errors: list[str] = []

    try:
        parsed = feedparser.parse(feed_url, request_headers={"User-Agent": "Mozilla/5.0"})
    except Exception as e:
        return FeedResult(feed_url=feed_url, episodes=[], errors=[str(e)])

    feed_meta = parsed.get("feed", {})
    show_name = _clean_html(feed_meta.get("title", "Unknown Show"))
    show_description = _clean_html(feed_meta.get("subtitle", "") or feed_meta.get("description", ""))

    for entry in parsed.entries:
        try:
            title = _clean_html(entry.get("title", "")).strip()
            description_raw = entry.get("summary", "") or entry.get("description", "")
            description = _clean_html(description_raw).strip()

            if not title or not description:
                errors.append(f"Skipped entry with missing title/description: {entry.get('id', 'unknown')}")
                continue

            episode_id = PodcastEpisode.compute_episode_id(show_name, title, description)

            transcript: Optional[str] = None
            if fetch_transcripts:
                transcript_url = _extract_transcript_url(description_raw)
                if transcript_url:
                    transcript = _fetch_transcript(transcript_url)

            episode = PodcastEpisode(
                episode_id=episode_id,
                show_name=show_name,
                title=title,
                description=description,
                transcript=transcript,
                duration_seconds=_parse_duration(entry),
                published_date=_parse_published_date(entry),
                show_description=show_description or None,
                language=None,  # set by normalizer
                episode_url=entry.get("link"),
                audio_url=_extract_audio_url(entry),
                raw_tags=[t.get("term", "") for t in entry.get("tags", []) if t.get("term")],
            )
            episodes.append(episode)

        except Exception as e:
            errors.append(f"Failed to parse entry '{entry.get('title', 'unknown')}': {e}")

    return FeedResult(feed_url=feed_url, episodes=episodes, errors=errors)


def fetch_feeds(feed_urls: list[str], fetch_transcripts: bool = False) -> Iterator[FeedResult]:
    for i, url in enumerate(feed_urls):
        logger.info(f"Fetching feed {i+1}/{len(feed_urls)}: {url}")
        yield fetch_feed(url, fetch_transcripts=fetch_transcripts)
        if i < len(feed_urls) - 1:
            time.sleep(FETCH_DELAY_SECONDS)
