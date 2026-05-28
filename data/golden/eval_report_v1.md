# Enrichment Evaluation Report

**Generated:** 2026-05-25 23:18 UTC  
**Prompt version:** v1  
**Schema version:** 1  
**Eval episodes:** 98

---

## Attribute Metrics

| Attribute | Precision | Recall | F1 | Notes |
|-----------|-----------|--------|----|-------|
| **mood** | 38.4% | 37.8% | **33.4%** | n=98 |
|   ↳ calm | 26.1% | 46.2% | 33.3% | support=13 |
|   ↳ energetic | 66.7% | 22.2% | 33.3% | support=9 |
|   ↳ humorous | 62.5% | 90.9% | 74.1% | support=11 |
|   ↳ inspirational | 16.7% | 40.0% | 23.5% | support=5 |
|   ↳ intense | 57.1% | 23.5% | 33.3% | support=17 |
|   ↳ melancholic | 0.0% | 0.0% | 0.0% | support=1 |
|   ↳ neutral | 9.1% | 33.3% | 14.3% | support=3 |
|   ↳ serious | 69.2% | 46.2% | 55.4% | support=39 |
| **difficulty** | 38.0% | 38.6% | **37.6%** | n=98 |
|   ↳ advanced | 0.0% | 0.0% | 0.0% | support=2 |
|   ↳ beginner | 52.5% | 68.9% | 59.6% | support=45 |
|   ↳ intermediate | 61.5% | 47.1% | 53.3% | support=51 |
| **format** | 37.5% | 38.1% | **32.0%** | n=98 |
|   ↳ educational_lecture | 0.0% | 0.0% | 0.0% | support=4 |
|   ↳ interview | 70.7% | 66.1% | 68.3% | support=62 |
|   ↳ narrative_storytelling | 90.0% | 37.5% | 52.9% | support=24 |
|   ↳ panel_discussion | 14.3% | 66.7% | 23.5% | support=3 |
|   ↳ solo_monologue | 12.5% | 20.0% | 15.4% | support=5 |
| **primary_topics** (P@3 / R@3) | 32.3% | 35.7% | — | n=98 |
| **best_listening_context** (P@4 / R@4) | 68.5% | 68.0% | — | n=98 |

## Free-Form Quality

| Metric | Value |
|--------|-------|
| BERTScore F1 (summary) | *skipped* |
| LLM hallucination rate | 0.0% (n=0) |
| Entity hallucination rate | 2.6% (n=98) |
| Entity F1 (key_entities) | 27.7% (P=23.7% R=33.2%) |

## Pipeline Health

| Metric | Value |
|--------|-------|
| Out-of-ontology topic rate | 0.0% |
| Dead letter rate | 2.0% |
| Avg processing time | 4616 ms/episode |
