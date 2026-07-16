# Feature-aware reranker v0.1.1

## Motivation

Dense retrieval improved semantic candidate recall but produced unsafe exact-product
links from shared brand or category meaning. The reranker combines dense and lexical
candidates with explicit catalog evidence instead of trusting cosine similarity as a
probability.

## Candidate features

For the union of lexical top-5 and dense top-5, the reranker records:

| Feature | Weight |
| --- | ---: |
| Explicit catalog alias boost | +0.30 |
| Explicit or phonetic brand evidence | 0.30 |
| Category compatibility | 0.15 |
| Model/family token overlap | 0.15 |
| Attribute agreement | 0.10 |
| Dense cosine | 0.20 |
| Lexical score | 0.10 |

The alias boost is additive and the combined score is capped at `1.0`. It fixes
explicit compact identifiers such as `15pm`, `s24u`, and `xm5` without lowering the
global acceptance threshold. Acceptance additionally requires:

- alias evidence, brand evidence, or model-token overlap of at least `0.25`;
- combined score of at least `0.40`;
- top-1 versus top-2 margin of at least `0.08`.

The original weights and thresholds were fixed before the first semantic-dev run.
Alias evidence was added in v0.1.1 after a public-demo false abstention and evaluated
without changing the acceptance thresholds. Every candidate's feature vector is
retained in the JSON report.

## Results

| Method | Accuracy@1 | Negative accuracy | End-to-end | Accepted precision | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lexical v0.2 | 0.100 | 0.800 | 0.240 | 0.667 | 0.120 |
| Dense MiniLM | 0.550 | 0.400 | 0.520 | 0.611 | 0.720 |
| Guarded hybrid | 0.150 | 0.800 | 0.280 | 0.750 | 0.160 |
| Feature reranker v0.1.1 | **0.900** | **1.000** | **0.920** | **1.000** | **0.720** |

Decision paths:

- accepted by feature reranker: 18;
- abstained without identity evidence: 5;
- abstained below score threshold: 2.

All five intentionally underspecified negatives were rejected. The reranker made no
accepted wrong link on this synthetic development set.

## Remaining failures

Both end-to-end errors were conservative abstentions with the correct top candidate:

- `флагман самсунг со стилусом серого цвета` → Galaxy S24 Ultra, score `0.372`;
- `сенхайзер с долгой батареей для поездок` → Momentum 4, score `0.394`.

The threshold was not lowered after observing these cases. A future catalog schema
should represent capabilities such as stylus support and battery-life classes. That
would add real evidence rather than tune a threshold to two known rows.

## Performance and limitations

The v0.1.1 verification run measured local CPU latency at p50 `20.4 ms` and p95
`22.1 ms`, dominated by MiniLM inference. Model loading took approximately `6.9 s`.

The result is a development result, not a final test metric. The dataset is small,
synthetic, and used to design the feature vocabulary. No frozen benchmark was rerun.
An independent human-reviewed holdout is required before claiming generalization.

## Reproduce

```bash
HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python \
  scripts/evaluate_semantic_reranker.py
```
