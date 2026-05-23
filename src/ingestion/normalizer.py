import logging
from typing import Optional

from langdetect import detect, LangDetectException

from src.schemas.episode import PodcastEpisode

logger = logging.getLogger(__name__)

MIN_DESCRIPTION_WORDS_FOR_LANG = 50


def detect_language(text: str) -> tuple[Optional[str], bool]:
    """Returns (language_code, is_confident)."""
    word_count = len(text.split())
    if word_count < MIN_DESCRIPTION_WORDS_FOR_LANG:
        return None, False
    try:
        lang = detect(text)
        return lang, True
    except LangDetectException:
        return None, False


def normalize_episode(episode: PodcastEpisode) -> PodcastEpisode:
    lang, confident = detect_language(episode.description)
    return episode.model_copy(update={"language": lang if confident else "uncertain"})


def is_english(episode: PodcastEpisode) -> bool:
    return episode.language in ("en", "uncertain")
