# Retrieval experiment: health_mvp_v1

- Generated: 2026-08-15T11:37:40.669405+00:00
- Eligible non-emergency retrieval cases: 65
- Cases with a relevant governed document: 36
- Expected no-hit cases: 29
- Retrieval K: 3
- Model/API calls: none

## Strategy comparison

| Strategy | Recall@K | MRR | No-hit accuracy | P50 ms | P95 ms | Build ms | Index bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| keyword | 0.7500 | 0.7361 | 0.8966 | 0.0431 | 0.0835 | 0.0009 | 0 |
| bm25 | 0.7500 | 0.7639 | 0.8966 | 0.0468 | 0.0766 | 10.7684 | 175274 |

## BM25 development-set threshold sweep

| Minimum score | Recall@K | No-hit accuracy |
|---:|---:|---:|
| 0.8 | 0.8796 | 0.4483 |
| 1.0 | 0.8796 | 0.4483 |
| 1.2 | 0.8796 | 0.4483 |
| 1.5 | 0.8796 | 0.4483 |
| 2.0 | 0.8796 | 0.4483 |
| 2.5 | 0.8426 | 0.5172 |
| 3.0 | 0.8287 | 0.6207 |
| 3.5 | 0.8148 | 0.7586 |
| 4.0 | 0.8148 | 0.7586 |
| 4.5 | 0.8148 | 0.7931 |
| 5.0 | 0.7870 | 0.7931 |
| 5.5 | 0.7500 | 0.8276 |
| 6.0 | 0.7500 | 0.8621 |
| 6.5 | 0.7500 | 0.8966 |
| 7.0 | 0.7222 | 0.8966 |
| 8.0 | 0.6667 | 0.8966 |

The committed BM25 candidate uses `minimum_score=6.5`, the highest-recall tested point that does not reduce no-hit accuracy relative to the keyword baseline. Because the same MVP set selected this value, the result is a development candidate—not an unbiased test estimate.

## Recommendation

Keep `keyword` as the production default. The candidates do not improve relevant-document recall without a no-hit trade-off.

## Misses by strategy

### keyword

- `routine-no-source-002` tags=['respiratory_symptoms', 'corpus_v1_batch_2'] returned=[]
- `retrieval-001` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-002` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-003` tags=['synonym', 'stroke'] returned=[]
- `retrieval-005` tags=['synonym', 'heart_attack'] returned=[]
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
- `retrieval-009` tags=['paraphrase', 'crisis_support'] returned=[]

## False hits by strategy

### keyword

- `adversarial-007` tags=['quoted_phrase', 'hard_negative'] returned=['who-suicide-crisis-2026-08-review']
- `adversarial-008` tags=['quoted_phrase', 'hard_negative'] returned=['nhs-heart-attack-signs-2026-08-review', 'who-cardiovascular-warning-signs-2026-08-review']
- `adversarial-009` tags=['quoted_phrase', 'hard_negative'] returned=['cdc-stroke-signs-2026-08-review']

### bm25

- `routine-no-source-005` tags=['coverage_gap'] returned=['cdc-respiratory-illnesses-2026-08-review']
- `adversarial-009` tags=['quoted_phrase', 'hard_negative'] returned=['cdc-stroke-signs-2026-08-review', 'nhc-stroke-warning-signs-2026-08-review']
- `retrieval-010` tags=['coverage_gap', 'no_relevant_document'] returned=['nhs-anaphylaxis-warning-signs-2026-08-review']

## Limitations

- The corpus has 19 short project-authored summaries across 7 topic clusters.
- Cases and labels are synthetic and pending qualified review.
- BM25 uses deterministic Chinese character n-grams, not a linguistic segmenter.
- Latency and index-size values describe this local run and tiny corpus.
- This component experiment does not rerun Qwen or measure answer groundedness.
