"""
Instructor-wrapped Anthropic client for structured enrichment output.
"""
import os

import anthropic
import instructor

_DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3  # validation retries passed to messages.create()


def get_enrichment_client(model: str = _DEFAULT_MODEL) -> tuple[instructor.Instructor, str]:
    """Return (instructor_client, model_name).

    max_retries is passed at call time (not here) to avoid a kwarg conflict
    between instructor's validation retries and Anthropic's HTTP retries.
    """
    api_key = (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ZAI_API_KEY")
        or os.environ.get("Z_AI_API_KEY")
    )
    if not api_key:
        raise EnvironmentError("Set ANTHROPIC_API_KEY or ZAI_API_KEY in environment")

    raw_client = anthropic.Anthropic(api_key=api_key)
    client = instructor.from_anthropic(raw_client)
    return client, model
