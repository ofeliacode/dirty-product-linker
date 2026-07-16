# Multi-product extraction candidate evaluation

## Status

This is a **synthetic candidate evaluation**, not the final human-reviewed holdout.
The role is stored as `synthetic_candidate` in both the pinned configuration and
generated report. These results may be used to diagnose the rule baseline, but not
as a claim of generalization.

## Fixed inputs

- 25 candidate queries and 30 linked product mentions;
- 10 explicit multi-product queries;
- 5 mentions embedded in longer context;
- 5 deliberately unseen surfaces;
- 5 negative queries without a concrete catalog product;
- demo catalog v0.2 with 20 products across five categories.

The configuration pins SHA-256 checksums for the dataset and catalog. The evaluator
refuses to run if either input changes.

## Metrics

| Metric | Result |
| --- | ---: |
| Exact span precision | 1.000 |
| Exact span recall | 0.833 |
| Exact span F1 | 0.909 |
| Linking accuracy on exact spans | 1.000 |
| End-to-end mention accuracy | 0.833 |
| Query exact match | 0.800 |
| Negative accuracy | 1.000 |

The extractor found all 25 mentions expressed with catalog aliases and linked every
found span correctly. It emitted no false positives on the negative slice. It missed
all five deliberately unseen surfaces, producing `0.000` recall on that slice.

This is the expected limitation of catalog surface matching: high precision and
transparent decisions, but no learned generalization beyond registered forms. The
result justifies the next experiment: compare the fixed rule baseline with a
token-classification mention detector while keeping the existing linker and
abstention policy.

## Reproduce

```bash
.venv/bin/python scripts/evaluate_multi_product_candidates.py
```

The command writes
`reports/development/multi_product_candidates_v0_1.json`, including every gold and
predicted span for error analysis.

## Promotion requirement

Before this becomes a final holdout, a person must inspect every query, product ID,
and half-open offset, correct unnatural wording, add genuinely authored queries, and
record a reviewer attestation. Until that happens, the candidate provenance remains
`synthetic` and the report remains under `reports/development/`.

Use the [human review checklist](multi-product-review-checklist.md) and the guarded
`scripts/promote_multi_product_holdout.py` command. Promotion requires an explicit
reviewer, date, and `--confirm-all`, and refuses to overwrite a frozen benchmark.
