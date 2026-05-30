# Enrichment Evaluation Report

**Generated:** 2026-05-30 19:26 UTC  
**Prompt version:** v5  
**Schema version:** 1  
**Eval episodes:** 100

---

## Attribute Metrics

| Attribute | Precision | Recall | F1 | Notes |
|-----------|-----------|--------|----|-------|
| **mood** | 34.4% | 37.4% | **34.1%** | n=100 |
|   ↳ calm | 35.7% | 33.3% | 34.5% | support=15 |
|   ↳ energetic | 33.3% | 11.1% | 16.7% | support=9 |
|   ↳ humorous | 75.0% | 81.8% | 78.3% | support=11 |
|   ↳ inspirational | 25.0% | 40.0% | 30.8% | support=5 |
|   ↳ intense | 43.5% | 58.8% | 50.0% | support=17 |
|   ↳ melancholic | 0.0% | 0.0% | 0.0% | support=1 |
|   ↳ neutral | 11.1% | 33.3% | 16.7% | support=3 |
|   ↳ serious | 51.6% | 41.0% | 45.7% | support=39 |
| **difficulty** | 43.8% | 43.9% | **43.4%** | n=100 |
|   ↳ advanced | 0.0% | 0.0% | 0.0% | support=2 |
|   ↳ beginner | 68.4% | 55.3% | 61.2% | support=47 |
|   ↳ intermediate | 62.9% | 76.5% | 69.0% | support=51 |
| **format** | 32.6% | 44.5% | **34.2%** | n=100 |
|   ↳ debate | 0.0% | 0.0% | 0.0% | support=0 |
|   ↳ educational_lecture | 0.0% | 0.0% | 0.0% | support=4 |
|   ↳ interview | 74.6% | 68.8% | 71.5% | support=64 |
|   ↳ narrative_storytelling | 73.7% | 58.3% | 65.1% | support=24 |
|   ↳ panel_discussion | 25.0% | 100.0% | 40.0% | support=3 |
|   ↳ solo_monologue | 22.2% | 40.0% | 28.6% | support=5 |
| **primary_topics** (P@3 / R@3) | 29.8% | 36.0% | — | n=100 |
| **best_listening_context** (P@4 / R@4) | 61.9% | 64.7% | — | n=100 |

## Free-Form Quality

| Metric | Value |
|--------|-------|
| BERTScore F1 (summary) | *skipped* |
| LLM hallucination rate | 0.0% (n=0) |
| Entity hallucination rate | 4.0% (n=100) |
| Entity F1 (key_entities) | 30.4% (P=27.6% R=33.9%) |

## Pipeline Health

| Metric | Value |
|--------|-------|
| Out-of-ontology topic rate | 0.0% |
| Dead letter rate | 0.0% |
| Avg processing time | 4657 ms/episode |
