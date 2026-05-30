# Enrichment Evaluation Report

**Generated:** 2026-05-28 05:12 UTC  
**Prompt version:** v3  
**Schema version:** 1  
**Eval episodes:** 99

---

## Attribute Metrics

| Attribute | Precision | Recall | F1 | Notes |
|-----------|-----------|--------|----|-------|
| **mood** | 42.5% | 35.6% | **32.9%** | n=99 |
|   ↳ calm | 41.2% | 46.7% | 43.8% | support=15 |
|   ↳ energetic | 100.0% | 11.1% | 20.0% | support=9 |
|   ↳ humorous | 81.8% | 81.8% | 81.8% | support=11 |
|   ↳ inspirational | 23.1% | 60.0% | 33.3% | support=5 |
|   ↳ intense | 41.7% | 58.8% | 48.8% | support=17 |
|   ↳ melancholic | 0.0% | 0.0% | 0.0% | support=1 |
|   ↳ neutral | 0.0% | 0.0% | 0.0% | support=3 |
|   ↳ serious | 52.6% | 26.3% | 35.1% | support=38 |
| **difficulty** | 43.8% | 44.6% | **44.2%** | n=99 |
|   ↳ advanced | 0.0% | 0.0% | 0.0% | support=2 |
|   ↳ beginner | 65.2% | 65.2% | 65.2% | support=46 |
|   ↳ intermediate | 66.0% | 68.6% | 67.3% | support=51 |
| **format** | 28.3% | 36.4% | **29.1%** | n=99 |
|   ↳ debate | 0.0% | 0.0% | 0.0% | support=0 |
|   ↳ educational_lecture | 0.0% | 0.0% | 0.0% | support=4 |
|   ↳ interview | 71.9% | 64.1% | 67.8% | support=64 |
|   ↳ narrative_storytelling | 61.1% | 47.8% | 53.7% | support=23 |
|   ↳ panel_discussion | 16.7% | 66.7% | 26.7% | support=3 |
|   ↳ solo_monologue | 20.0% | 40.0% | 26.7% | support=5 |
| **primary_topics** (P@3 / R@3) | 30.3% | 34.3% | — | n=99 |
| **best_listening_context** (P@4 / R@4) | 62.1% | 59.6% | — | n=99 |

## Free-Form Quality

| Metric | Value |
|--------|-------|
| BERTScore F1 (summary) | *skipped* |
| LLM hallucination rate | 0.0% (n=0) |
| Entity hallucination rate | 2.0% (n=99) |
| Entity F1 (key_entities) | 29.9% (P=27.6% R=32.6%) |

## Pipeline Health

| Metric | Value |
|--------|-------|
| Out-of-ontology topic rate | 0.0% |
| Dead letter rate | 1.0% |
| Avg processing time | 4736 ms/episode |
