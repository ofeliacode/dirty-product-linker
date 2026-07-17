# AI-authored 100-query challenge set

`data/benchmark/candidates/ai_challenge_v0_1.jsonl` is a deliberately broad candidate
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

The queries were authored by an AI assistant and have `provenance=synthetic`. They
are appropriate for challenge-driven development, annotation review, and error
analysis. They are **not** a human-authored independent holdout and must not be used
to claim human-distribution generalization.

Do not add the challenge strings to normalization rules or catalog aliases before
the first baseline evaluation. Doing so would leak expected inputs into the system.

## Reproduce and validate

The source specification and deterministic offset generation live in
`scripts/create_ai_challenge_set.py`:

```bash
PYTHONPATH=src .venv/bin/python scripts/create_ai_challenge_set.py
.venv/bin/pytest -q tests/test_ai_challenge_data.py
```

The test validates the slice counts, unique query IDs, exact half-open character
offsets, synthetic provenance, and every `product_id` against demo catalog v0.2.

## Next evaluation step

1. Commit the candidate set before running inference.
2. Run the current extractor once and save an immutable baseline report.
3. Inspect errors by slice, especially abstention and unseen abbreviations.
4. Keep the dataset separate from training and alias expansion.
5. Independently collect new human-authored queries for the final portfolio metric.

