# Retrieval experiment: health_mvp_v1

- Generated: 2026-08-12T08:27:06.806204+00:00
- Eligible non-emergency retrieval cases: 55
- Cases with a relevant governed document: 24
- Expected no-hit cases: 31
- Retrieval K: 3
- Model/API calls: none

## Strategy comparison

| Strategy | Recall@K | MRR | No-hit accuracy | P50 ms | P95 ms | Build ms | Index bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| keyword | 0.6250 | 0.6250 | 0.9032 | 0.0061 | 0.0127 | 0.0009 | 0 |
| bm25 | 0.7083 | 0.7083 | 0.9677 | 0.0137 | 0.0194 | 1.5755 | 15967 |

## BM25 development-set threshold sweep

| Minimum score | Recall@K | No-hit accuracy |
|---:|---:|---:|
| 0.8 | 0.9583 | 0.8065 |
| 1.0 | 0.8750 | 0.8065 |
| 1.2 | 0.8333 | 0.8387 |
| 1.5 | 0.7917 | 0.8710 |
| 2.0 | 0.7083 | 0.9677 |
| 2.5 | 0.6667 | 0.9677 |
| 3.0 | 0.6250 | 0.9677 |

The committed BM25 candidate uses `minimum_score=2.0`, the highest-recall tested point that does not reduce no-hit accuracy relative to the keyword baseline. Because the same MVP set selected this value, the result is a development candidate—not an unbiased test estimate.

## Recommendation

Promote `bm25` to the next candidate gate: it improves Recall@3 by 0.0833 without reducing no-hit accuracy. Keep `keyword` as the production default until an independent holdout confirms the development-set result; the separate end-to-end comparison is recorded alongside this report.

## Misses by strategy

### keyword

- `retrieval-001` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-002` tags=['paraphrase', 'stroke'] returned=[]
- `retrieval-003` tags=['synonym', 'stroke'] returned=[]
- `retrieval-004` tags=['paraphrase', 'heart_attack'] returned=[]
- `retrieval-005` tags=['synonym', 'heart_attack'] returned=[]
- `retrieval-006` tags=['paraphrase', 'heart_attack'] returned=[]
- `retrieval-007` tags=['paraphrase', 'crisis_support'] returned=[]
- `retrieval-008` tags=['paraphrase', 'crisis_support'] returned=[]
- `retrieval-009` tags=['paraphrase', 'crisis_support'] returned=[]

### bm25

- `routine-crisis-005` tags=['crisis_support', 'informational'] returned=[]
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

- `adversarial-009` tags=['quoted_phrase', 'hard_negative'] returned=['cdc-stroke-signs-2026-08-review']

## Limitations

- The corpus has only three short project-authored summaries.
- Cases and labels are synthetic and pending qualified review.
- BM25 uses deterministic Chinese character n-grams, not a linguistic segmenter.
- Latency and index-size values describe this local run and tiny corpus.
- This component experiment does not rerun Qwen or measure answer groundedness.
