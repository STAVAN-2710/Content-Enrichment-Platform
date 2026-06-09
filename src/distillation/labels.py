import numpy as np

MOOD_VOCAB = sorted(["calm", "energetic", "humorous", "inspirational", "intense", "melancholic", "neutral", "serious"])
DIFFICULTY_VOCAB = sorted(["advanced", "beginner", "intermediate"])
FORMAT_VOCAB = sorted(["debate", "educational_lecture", "interview", "narrative_storytelling", "panel_discussion", "solo_monologue"])
LISTENING_CONTEXT_VOCAB = sorted(["casual_listening", "commute", "cooking", "deep_work", "learning", "sleep", "social", "workout"])
TOPIC_VOCAB = sorted([
    "ancient_history", "arts_and_entertainment", "artificial_intelligence", "astronomy",
    "biology", "career", "climate_and_environment", "comedy", "cultural_history",
    "cybercrime", "cybersecurity", "data_science", "economics", "entrepreneurship",
    "ethics", "fitness", "habits_and_mindset", "hardware", "investing", "leadership",
    "longevity", "marketing", "mathematics", "media_and_journalism", "medicine",
    "mental_health", "military_history", "modern_history", "mythology", "neuroscience",
    "nutrition", "paleontology", "personal_finance", "philosophy_of_mind", "physics",
    "planetary_science", "political_commentary", "political_history", "politics",
    "productivity", "relationships", "satire", "sleep", "social_issues",
    "software_engineering", "spirituality", "sports", "startups_and_vc",
    "surveillance_and_privacy", "true_crime",
])

SINGLE_LABEL_FIELDS = ("mood", "difficulty", "format")
MULTI_LABEL_FIELDS = ("primary_topics", "secondary_topics", "best_listening_context")
ALL_FIELDS = SINGLE_LABEL_FIELDS + MULTI_LABEL_FIELDS

_VOCABS = {
    "mood": MOOD_VOCAB,
    "difficulty": DIFFICULTY_VOCAB,
    "format": FORMAT_VOCAB,
    "best_listening_context": LISTENING_CONTEXT_VOCAB,
    "primary_topics": TOPIC_VOCAB,
    "secondary_topics": TOPIC_VOCAB,
}


class LabelEncoders:
    def vocab_size(self, field: str) -> int:
        return len(_VOCABS[field])

    def is_multi(self, field: str) -> bool:
        return field in MULTI_LABEL_FIELDS

    def encode_single(self, field: str, value: str) -> int:
        vocab = _VOCABS[field]
        if value not in vocab:
            raise ValueError(f"Unknown label {value!r} for field {field!r}")
        return vocab.index(value)

    def decode_single(self, field: str, idx: int) -> str:
        return _VOCABS[field][idx]

    def encode_multi(self, field: str, values: list[str]) -> np.ndarray:
        vocab = _VOCABS[field]
        vec = np.zeros(len(vocab), dtype=np.float32)
        for v in values:
            if v not in vocab:
                raise ValueError(f"Unknown label {v!r} for field {field!r}")
            vec[vocab.index(v)] = 1.0
        return vec

    def decode_multi(self, field: str, binarized: np.ndarray, threshold: float = 0.5) -> list[str]:
        vocab = _VOCABS[field]
        return [vocab[i] for i, v in enumerate(binarized) if v >= threshold]
