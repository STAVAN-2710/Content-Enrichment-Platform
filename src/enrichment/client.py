"""
Instructor-wrapped OpenAI client for structured enrichment output.

Prefers OPENAI_API_KEY (api.openai.com). Falls back to ZAI_API_KEY with custom base_url.
Instructor wraps it for Pydantic schema enforcement + auto-retry on validation failure.
"""
import os

import instructor
import openai

# gpt-4o-mini: best cost/quality for structured extraction tasks
_DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
_ZAI_BASE_URL = "https://api.z.ai/api/v1"
MAX_RETRIES = 3  # validation retries passed to chat.completions.create()


def get_enrichment_client(model: str | None = None) -> tuple[instructor.Instructor, str]:
    """Return (instructor_client, model_name).

    Uses OPENAI_API_KEY → api.openai.com by default.
    Falls back to ZAI_API_KEY → ZAI_BASE_URL if OPENAI_API_KEY not set.
    """
    resolved_model = model or _DEFAULT_MODEL

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        raw_client = openai.OpenAI(api_key=openai_key)
        return instructor.from_openai(raw_client), resolved_model

    zai_key = os.environ.get("ZAI_API_KEY") or os.environ.get("Z_AI_API_KEY")
    if zai_key:
        base_url = os.environ.get("ZAI_BASE_URL", _ZAI_BASE_URL)
        raw_client = openai.OpenAI(api_key=zai_key, base_url=base_url)
        return instructor.from_openai(raw_client), resolved_model

    raise EnvironmentError("Set OPENAI_API_KEY or ZAI_API_KEY in environment")
