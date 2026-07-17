# Synthetic 100-query challenge set

`data/benchmark/candidates/synthetic_challenge_v0_1.jsonl` is a deliberately broad
candidate
set for product mention extraction and entity linking. It contains 100 Russian or
Russian/English mixed queries in the requested distribution:

| Slice | Count | Purpose |
| --- | ---: | --- |
| `ordinary_single` | 20 | One explicitly named catalog product |
| `slang_and_typos` | 20 | Misspellings, colloquialisms, and transliteration |
| `multi_product` | 20 | Two or three independently labelled products |
| `ambiguous` | 15 | Partial descriptions and cases that should abstain |
| `negative` | 15 | No specific catalog product |
| `unseen_abbreviation` | 10 | Abbreviations absent from catalog aliases |

## Status and allowed use

The queries are synthetic and have `provenance=synthetic`. They are appropriate for
challenge-driven development, annotation review, and error analysis. They are
**not** a human-authored independent holdout and must not be used to claim
human-distribution generalization.

Do not add the challenge strings to normalization rules or catalog aliases before
the first baseline evaluation. Doing so would leak expected inputs into the system.

## Reproduce and validate

The source specification and deterministic offset generation live in
`scripts/create_synthetic_challenge_set.py`:

```bash
PYTHONPATH=src .venv/bin/python scripts/create_synthetic_challenge_set.py
.venv/bin/pytest -q tests/test_synthetic_challenge_data.py
```

The test validates the slice counts, unique query IDs, exact half-open character
offsets, synthetic provenance, and every `product_id` against demo catalog v0.2.

## Frozen baseline result

The candidate set was committed before inference. The existing
`catalog-longest-surface-v0.1` extractor was then run once with the pinned config in
`configs/eval/synthetic_challenge_v0_1.yaml`. The complete predictions are stored in
`reports/development/synthetic_challenge_v0_1_baseline.json`.

| Slice | Query exact match | End-to-end mention accuracy | Exact-span precision |
| --- | ---: | ---: | ---: |
| Overall | 0.510 | 0.447 | 0.958 |
| Ordinary single | 0.950 | 0.950 | 0.950 |
| Slang and typos | 0.000 | 0.000 | 0.000 |
| Multiple products | 0.500 | 0.600 | 0.964 |
| Ambiguous | 0.467 | 0.000 | 0.000 |
| Negative | 1.000 | n/a | n/a |
| Unseen abbreviation | 0.000 | 0.000 | 0.000 |

Overall exact-span F1 is `0.609`; linking accuracy on the 46 exact spans found is
`1.000`; negative accuracy is `1.000`. Zero-valued mention metrics on negative
queries mean there are no positive mentions to score, not that abstention failed.

## Error analysis

The baseline links a product correctly whenever it finds the exact mention, but it
only recalls `46/103` gold mentions. This isolates mention detection as the main
bottleneck:

- all 20 typo/slang mentions were missed;
- all 10 deliberately unseen abbreviations were missed;
- 18 of 45 mentions in multi-product queries were missed;
- all 8 positive mentions in the ambiguous slice were missed;
- all 15 negative queries and all 7 unanswerable ambiguous queries were safely left
  empty;
- one ordinary query used `LG OLED C3` as the gold span while the catalog surface
  matcher selected the longer `LG OLED C3 55`, producing an exact-boundary error.

These results support building an uncertainty-aware learned mention extractor rather
than copying challenge strings into the catalog alias list. The dataset must remain
separate from training. A future human-authored holdout is still required for the
final portfolio generalization claim.

Reproduce the pinned baseline with:

```bash
.venv/bin/python scripts/evaluate_multi_product_candidates.py \
  --config configs/eval/synthetic_challenge_v0_1.yaml
```
