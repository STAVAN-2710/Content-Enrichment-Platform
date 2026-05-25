"""
Hallucination detection — two complementary checks:

1. LLM-as-Judge: sends (source_text, generated_summary) to Claude and asks
   whether the summary makes claims unsupported by the source. Returns a
   structured verdict with a reasoning string.

2. Entity hallucination check: verifies that each named entity in key_entities
   appears in the source text (after normalization). String-level check, fast
   and cheap — catches the most common failure mode (invented proper nouns).
"""
import os
import re

import anthropic

from src.evaluation.metrics import normalize_entity

_JUDGE_MODEL = "claude-haiku-4-5-20251001"  # cheap model for judge calls

_JUDGE_SYSTEM = """You are a factual consistency evaluator for a podcast enrichment system.

Given a source text (podcast episode description/transcript) and a generated summary,
determine whether the summary contains any factual claims that are:
  - Contradicted by the source text, OR
  - Not supported by the source text (invented facts)

Respond with a JSON object:
{
  "is_hallucination": true | false,
  "reasoning": "one sentence explanation",
  "severity": "none" | "minor" | "major"
}

minor: claim could be inferred but is not explicit in source
major: claim directly contradicts source or invents a specific fact (name, date, number)
"""


def _get_anthropic_client() -> anthropic.Anthropic:
    api_key = (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ZAI_API_KEY")
        or os.environ.get("Z_AI_API_KEY")
    )
    if not api_key:
        raise EnvironmentError("Set ANTHROPIC_API_KEY or Z_AI_API_KEY")
    return anthropic.Anthropic(api_key=api_key)


def llm_judge_hallucination(
    source_text: str,
    generated_summary: str,
    client: anthropic.Anthropic | None = None,
) -> dict:
    """Call Claude Haiku to judge factual consistency.

    Returns dict with keys: is_hallucination (bool), reasoning (str), severity (str).
    Falls back to {'is_hallucination': None, 'error': ...} on API failure.
    """
    import json

    if client is None:
        client = _get_anthropic_client()

    user_msg = (
        f"SOURCE TEXT:\n{source_text[:3000]}\n\n"
        f"GENERATED SUMMARY:\n{generated_summary}\n\n"
        "Does the summary contain any factual claims unsupported by or contradicting the source?"
    )

    try:
        response = client.messages.create(
            model=_JUDGE_MODEL,
            max_tokens=256,
            system=_JUDGE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text.strip()
        # Extract JSON from response (model sometimes adds prose)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {"is_hallucination": None, "error": f"no JSON in response: {raw[:100]}"}
    except Exception as exc:
        return {"is_hallucination": None, "error": str(exc)}


def check_entity_hallucination(
    source_text: str,
    entities: list[str],
) -> dict:
    """Check which entities do NOT appear in source_text.

    Returns:
      hallucinated: list of entities not found in source
      verified: list of entities confirmed in source
      hallucination_rate: fraction hallucinated
    """
    source_lower = source_text.lower()
    hallucinated, verified = [], []

    for entity in entities:
        norm = normalize_entity(entity)
        if not norm:
            continue
        if norm in source_lower:
            verified.append(entity)
        else:
            hallucinated.append(entity)

    total = len(hallucinated) + len(verified)
    rate = len(hallucinated) / total if total > 0 else 0.0

    return {
        "hallucinated": hallucinated,
        "verified": verified,
        "hallucination_rate": round(rate, 4),
    }


def batch_hallucination_check(
    records: list[dict],
    source_texts: dict[str, str],
    run_llm_judge: bool = True,
    client: anthropic.Anthropic | None = None,
) -> dict:
    """Run hallucination checks on a batch of enrichment records.

    Args:
        records: list of enrichment dicts (must have episode_id, summary_one_sentence, key_entities)
        source_texts: episode_id → text_for_enrichment
        run_llm_judge: set False to skip LLM-as-Judge (entity check only, faster/cheaper)

    Returns aggregate stats + per-episode detail.
    """
    if client is None and run_llm_judge:
        client = _get_anthropic_client()

    per_episode = []
    entity_rates = []
    llm_hallucinations = 0
    llm_checked = 0

    for rec in records:
        ep_id = rec["episode_id"]
        source = source_texts.get(ep_id, "")
        summary = rec.get("summary_one_sentence", "")
        entities = rec.get("key_entities", [])

        entity_result = check_entity_hallucination(source, entities)
        entity_rates.append(entity_result["hallucination_rate"])

        llm_result = None
        if run_llm_judge and source and summary:
            llm_result = llm_judge_hallucination(source, summary, client=client)
            if llm_result.get("is_hallucination") is True:
                llm_hallucinations += 1
            if llm_result.get("is_hallucination") is not None:
                llm_checked += 1

        per_episode.append({
            "episode_id": ep_id,
            "entity_hallucination": entity_result,
            "llm_judge": llm_result,
        })

    return {
        "overall_llm_hallucination_rate": round(
            llm_hallucinations / max(llm_checked, 1), 4
        ),
        "overall_entity_hallucination_rate": round(
            sum(entity_rates) / max(len(entity_rates), 1), 4
        ),
        "llm_judge_n": llm_checked,
        "entity_check_n": len(records),
        "per_episode": per_episode,
    }
