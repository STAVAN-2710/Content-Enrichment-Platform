import hashlib
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class PodcastEpisode(BaseModel):
    # Identity
    episode_id: str
    show_name: str

    # Content
    title: str
    description: str
    transcript: Optional[str] = None
    duration_seconds: Optional[int] = None

    # Metadata
    published_date: Optional[datetime] = None
    show_description: Optional[str] = None
    language: Optional[str] = None
    episode_url: Optional[str] = None
    audio_url: Optional[str] = None

    # Weak signal only — never used as ground truth
    raw_tags: list[str] = Field(default_factory=list)

    # Pipeline metadata
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: int = 1

    @computed_field
    @property
    def text_for_enrichment(self) -> str:
        if self.transcript:
            return f"Title: {self.title}\n\nTranscript:\n{self.transcript[:8000]}"
        return f"Title: {self.title}\n\nDescription:\n{self.description}"

    @staticmethod
    def compute_episode_id(show_name: str, title: str, description: str) -> str:
        content = f"{show_name}|{title}|{description[:200]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
