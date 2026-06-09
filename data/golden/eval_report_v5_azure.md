# Enrichment Evaluation Report

**Generated:** 2026-05-30 20:55 UTC  
**Prompt version:** v5  
**Schema version:** 1  
**Eval episodes:** 99

---

## Attribute Metrics

| Attribute | Precision | Recall | F1 | Notes |
|-----------|-----------|--------|----|-------|
| **mood** | 27.3% | 32.3% | **28.4%** | n=99 |
|   ↳ calm | 33.3% | 33.3% | 33.3% | support=15 |
|   ↳ energetic | 0.0% | 0.0% | 0.0% | support=9 |
|   ↳ humorous | 72.7% | 72.7% | 72.7% | support=11 |
|   ↳ inspirational | 14.3% | 20.0% | 16.7% | support=5 |
|   ↳ intense | 44.0% | 64.7% | 52.4% | support=17 |
|   ↳ melancholic | 0.0% | 0.0% | 0.0% | support=1 |
|   ↳ neutral | 7.7% | 33.3% | 12.5% | support=3 |
|   ↳ serious | 46.4% | 34.2% | 39.4% | support=38 |
| **difficulty** | 43.8% | 44.4% | **43.9%** | n=99 |
|   ↳ advanced | 0.0% | 0.0% | 0.0% | support=2 |
|   ↳ beginner | 65.8% | 58.7% | 62.1% | support=46 |
|   ↳ intermediate | 65.5% | 74.5% | 69.7% | support=51 |
| **format** | 29.5% | 33.6% | **29.9%** | n=99 |
|   ↳ educational_lecture | 0.0% | 0.0% | 0.0% | support=4 |
|   ↳ interview | 70.2% | 62.5% | 66.1% | support=64 |
|   ↳ narrative_storytelling | 54.5% | 52.2% | 53.3% | support=23 |
|   ↳ panel_discussion | 8.3% | 33.3% | 13.3% | support=3 |
|   ↳ solo_monologue | 14.3% | 20.0% | 16.7% | support=5 |
| **primary_topics** (P@3 / R@3) | 24.9% | 29.3% | — | n=99 |
| **best_listening_context** (P@4 / R@4) | 67.1% | 71.2% | — | n=99 |

## Free-Form Quality

| Metric | Value |
|--------|-------|
| BERTScore F1 (summary) | *skipped* |
| LLM hallucination rate | 0.0% (n=0) |
| Entity hallucination rate | 2.5% (n=99) |
| Entity F1 (key_entities) | 30.5% (P=27.6% R=34.1%) |

## Pipeline Health

| Metric | Value |
|--------|-------|
| Out-of-ontology topic rate | 0.0% |
| Dead letter rate | 1.0% |
| Avg processing time | 2977 ms/episode |
