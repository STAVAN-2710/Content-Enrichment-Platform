# Enrichment Evaluation Report

**Generated:** 2026-05-28 02:05 UTC  
**Prompt version:** v2  
**Schema version:** 1  
**Eval episodes:** 97

---

## Attribute Metrics

| Attribute | Precision | Recall | F1 | Notes |
|-----------|-----------|--------|----|-------|
| **mood** | 37.6% | 41.2% | **33.0%** | n=97 |
|   ↳ calm | 33.3% | 33.3% | 33.3% | support=15 |
|   ↳ energetic | 50.0% | 12.5% | 20.0% | support=8 |
|   ↳ humorous | 83.3% | 90.9% | 87.0% | support=11 |
|   ↳ inspirational | 25.0% | 60.0% | 35.3% | support=5 |
|   ↳ intense | 42.1% | 47.1% | 44.4% | support=17 |
|   ↳ melancholic | 0.0% | 0.0% | 0.0% | support=1 |
|   ↳ neutral | 8.7% | 66.7% | 15.4% | support=3 |
|   ↳ serious | 58.3% | 18.9% | 28.6% | support=37 |
| **difficulty** | 41.9% | 42.9% | **42.4%** | n=97 |
|   ↳ advanced | 0.0% | 0.0% | 0.0% | support=2 |
|   ↳ beginner | 60.4% | 65.9% | 63.0% | support=44 |
|   ↳ intermediate | 65.3% | 62.7% | 64.0% | support=51 |
| **format** | 31.4% | 38.6% | **33.0%** | n=97 |
|   ↳ educational_lecture | 0.0% | 0.0% | 0.0% | support=4 |
|   ↳ interview | 71.7% | 60.3% | 65.5% | support=63 |
|   ↳ narrative_storytelling | 54.2% | 59.1% | 56.5% | support=22 |
|   ↳ panel_discussion | 9.1% | 33.3% | 14.3% | support=3 |
|   ↳ solo_monologue | 22.2% | 40.0% | 28.6% | support=5 |
| **primary_topics** (P@3 / R@3) | 23.7% | 46.4% | — | n=97 |
| **best_listening_context** (P@4 / R@4) | 63.9% | 62.5% | — | n=97 |

## Free-Form Quality

| Metric | Value |
|--------|-------|
| BERTScore F1 (summary) | *skipped* |
| LLM hallucination rate | 0.0% (n=0) |
| Entity hallucination rate | 2.7% (n=97) |
| Entity F1 (key_entities) | 30.1% (P=27.6% R=33.1%) |

## Pipeline Health

| Metric | Value |
|--------|-------|
| Out-of-ontology topic rate | 0.0% |
| Dead letter rate | 3.0% |
| Avg processing time | 4774 ms/episode |
