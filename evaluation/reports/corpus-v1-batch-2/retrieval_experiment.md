# Retrieval experiment: health_mvp_v1

- Generated: 2026-08-14T08:07:50.684043+00:00
- Eligible non-emergency retrieval cases: 55
- Cases with a relevant governed document: 26
- Expected no-hit cases: 29
- Retrieval K: 3
- Model/API calls: none

## Strategy comparison

| Strategy | Recall@K | MRR | No-hit accuracy | P50 ms | P95 ms | Build ms | Index bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| keyword | 0.6154 | 0.5962 | 0.8966 | 0.0190 | 0.0440 | 0.0008 | 0 |
| bm25 | 0.6538 | 0.6346 | 0.8966 | 0.0238 | 0.0341 | 4.7070 | 73956 |

## BM25 development-set threshold sweep

| Minimum score | Recall@K | No-hit accuracy |
|---:|---:|---:|
| 0.8 | 0.9231 | 0.6207 |
| 1.0 | 0.8846 | 0.6207 |
| 1.2 | 0.8462 | 0.6207 |
| 1.5 | 0.8077 | 0.6207 |
| 2.0 | 0.7500 | 0.7241 |
| 2.5 | 0.7308 | 0.7931 |
| 3.0 | 0.7308 | 0.7931 |
| 3.5 | 0.6923 | 0.8276 |
| 4.0 | 0.6538 | 0.8966 |

The committed BM25 candidate uses `minimum_score=4.0`, the highest-recall tested point that does not reduce no-hit accuracy relative to the keyword baseline. Because the same MVP set selected this value, the result is a development candidate—not an unbiased test estimate.

## Recommendation

Promote `bm25` to the next candidate gate: it improves Recall@3 by 0.0385 without reducing no-hit accuracy. Keep `keyword` as the production default until an independent holdout confirms the development-set result; the separate end-to-end comparison is recorded alongside this report.

## Misses by strategy

### keyword

- `routine-no-source-002` tags=['respiratory_symptoms', 'corpus_v1_batch_2'] returned=[]
- `retrieval-001` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-002` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-003` tags=['synonym', 'stroke'] returned=[]
- `retrieval-004` tags=['paraphrase', 'heart_attack'] returned=['cdc-respiratory-illnesses-2026-08-review']
- `retrieval-005` tags=['synonym', 'heart_attack'] returned=[]
- `retrieval-006` tags=['paraphrase', 'heart_attack'] returned=[]
- `retrieval-007` tags=['paraphrase', 'crisis_support'] returned=[]
- `retrieval-008` tags=['paraphrase', 'crisis_support'] returned=[]
- `retrieval-009` tags=['paraphrase', 'crisis_support'] returned=[]

### bm25

- `routine-crisis-005` tags=['crisis_support', 'informational'] returned=[]
- `routine-no-source-001` tags=['corpus_v1_batch_1', 'gastrointestinal_symptoms'] returned=[]
- `routine-no-source-002` tags=['respiratory_symptoms', 'corpus_v1_batch_2'] returned=['who-diarrhoeal-disease-2026-08-review']
- `retrieval-001` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-002` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-003` tags=['synonym', 'stroke'] returned=[]
- `retrieval-005` tags=['synonym', 'heart_attack'] returned=[]
- `retrieval-006` tags=['paraphrase', 'heart_attack'] returned=[]
- `retrieval-009` tags=['paraphrase', 'crisis_support'] returned=[]

## False hits by strategy

### keyword

- `adversarial-007` tags=['quoted_phrase', 'hard_negative'] returned=['who-suicide-crisis-2026-08-review']
- `adversarial-008` tags=['quoted_phrase', 'hard_negative'] returned=['nhs-heart-attack-signs-2026-08-review']
- `adversarial-009` tags=['quoted_phrase', 'hard_negative'] returned=['cdc-stroke-signs-2026-08-review']

### bm25

- `routine-no-source-005` tags=['coverage_gap'] returned=['cdc-respiratory-illnesses-2026-08-review']
- `adversarial-006` tags=['quoted_phrase', 'hard_negative'] returned=['nhs-shortness-of-breath-2026-08-review']
- `adversarial-009` tags=['quoted_phrase', 'hard_negative'] returned=['cdc-stroke-signs-2026-08-review']

## Limitations

- The corpus has nine short project-authored summaries across five topic clusters.
- Cases and labels are synthetic and pending qualified review.
- BM25 uses deterministic Chinese character n-grams, not a linguistic segmenter.
- Latency and index-size values describe this local run and tiny corpus.
- This component experiment does not rerun Qwen or measure answer groundedness.
