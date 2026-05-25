"""
Instructor-wrapped Anthropic client for structured enrichment output.
"""
import os

import anthropic
import instructor

_DEFAULT_MODEL = "claude-sonnet-4-6"
_MAX_RETRIES = 3


def get_enrichment_client(model: str = _DEFAULT_MODEL) -> tuple[instructor.Instructor, str]:
    """Return (instructor_client, model_name).

    Instructor will automatically retry up to _MAX_RETRIES times when the LLM
    returns a value that fails Pydantic validation, feeding the error back as
    a correction message.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("Z_AI_API_KEY")
    if not api_key:
        raise EnvironmentError("Set ANTHROPIC_API_KEY or Z_AI_API_KEY in environment")

    raw_client = anthropic.Anthropic(api_key=api_key)
    client = instructor.from_anthropic(raw_client, max_retries=_MAX_RETRIES)
    return client, model
