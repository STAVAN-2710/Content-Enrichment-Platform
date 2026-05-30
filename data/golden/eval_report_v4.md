# Enrichment Evaluation Report

**Generated:** 2026-05-30 05:35 UTC  
**Prompt version:** v4  
**Schema version:** 1  
**Eval episodes:** 99

---

## Attribute Metrics

| Attribute | Precision | Recall | F1 | Notes |
|-----------|-----------|--------|----|-------|
| **mood** | 35.7% | 37.3% | **34.8%** | n=99 |
|   ↳ calm | 16.7% | 7.1% | 10.0% | support=14 |
|   ↳ energetic | 50.0% | 22.2% | 30.8% | support=9 |
|   ↳ humorous | 81.8% | 81.8% | 81.8% | support=11 |
|   ↳ inspirational | 25.0% | 40.0% | 30.8% | support=5 |
|   ↳ intense | 40.0% | 70.6% | 51.1% | support=17 |
|   ↳ melancholic | 0.0% | 0.0% | 0.0% | support=1 |
|   ↳ neutral | 25.0% | 33.3% | 28.6% | support=3 |
|   ↳ serious | 47.2% | 43.6% | 45.3% | support=39 |
| **difficulty** | 44.2% | 44.2% | **43.5%** | n=99 |
|   ↳ advanced | 0.0% | 0.0% | 0.0% | support=2 |
|   ↳ beginner | 68.6% | 52.2% | 59.3% | support=46 |
|   ↳ intermediate | 64.1% | 80.4% | 71.3% | support=51 |
| **format** | 30.5% | 38.1% | **31.2%** | n=99 |
|   ↳ debate | 0.0% | 0.0% | 0.0% | support=0 |
|   ↳ educational_lecture | 0.0% | 0.0% | 0.0% | support=4 |
|   ↳ interview | 72.7% | 63.5% | 67.8% | support=63 |
|   ↳ narrative_storytelling | 70.0% | 58.3% | 63.6% | support=24 |
|   ↳ panel_discussion | 15.4% | 66.7% | 25.0% | support=3 |
|   ↳ solo_monologue | 25.0% | 40.0% | 30.8% | support=5 |
| **primary_topics** (P@3 / R@3) | 28.3% | 35.4% | — | n=99 |
| **best_listening_context** (P@4 / R@4) | 62.0% | 66.2% | — | n=99 |

## Free-Form Quality

| Metric | Value |
|--------|-------|
| BERTScore F1 (summary) | *skipped* |
| LLM hallucination rate | 0.0% (n=0) |
| Entity hallucination rate | 3.5% (n=99) |
| Entity F1 (key_entities) | 30.0% (P=26.4% R=34.6%) |

## Pipeline Health

| Metric | Value |
|--------|-------|
| Out-of-ontology topic rate | 0.0% |
| Dead letter rate | 1.0% |
| Avg processing time | 4525 ms/episode |
