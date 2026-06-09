"""
Instructor-wrapped OpenAI client for structured enrichment output.

Priority: AZURE_OPENAI_API_KEY → OPENAI_API_KEY → ZAI_API_KEY.
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

    Priority: AZURE_OPENAI_API_KEY → OPENAI_API_KEY → ZAI_API_KEY.
    Azure: model name is the deployment name (AZURE_OPENAI_DEPLOYMENT).
    """
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if azure_key:
        endpoint = (os.environ.get("AZURE_OPENAI_ENDPOINT") or os.environ.get("AZURE_OPENAI_BASE_URL", "")).rstrip("/")
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        # Endpoint already contains /openai/v1 — use directly as base_url (OpenAI-compatible mode)
        raw_client = openai.OpenAI(
            api_key=azure_key,
            base_url=endpoint,
            max_retries=8,
        )
        return instructor.from_openai(raw_client), deployment

    resolved_model = model or _DEFAULT_MODEL

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        # max_retries=8: OpenAI client retries 429/5xx with exponential backoff automatically
        raw_client = openai.OpenAI(api_key=openai_key, max_retries=8)
        return instructor.from_openai(raw_client), resolved_model

    zai_key = os.environ.get("ZAI_API_KEY") or os.environ.get("Z_AI_API_KEY")
    if zai_key:
        base_url = os.environ.get("ZAI_BASE_URL", _ZAI_BASE_URL)
        raw_client = openai.OpenAI(api_key=zai_key, base_url=base_url, max_retries=8)
        return instructor.from_openai(raw_client), resolved_model

    raise EnvironmentError("Set AZURE_OPENAI_API_KEY, OPENAI_API_KEY, or ZAI_API_KEY in environment")
