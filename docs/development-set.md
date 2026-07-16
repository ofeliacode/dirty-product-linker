# Synthetic retrieval development set v0.1

## Purpose

`data/development/retrieval_dev_v0_1.jsonl` is the dataset on which lexical rules,
normalization, and thresholds may be changed. It is not a final test set and must not
be presented as independent evidence of model quality.

The set contains 24 synthetic queries:

- 18 answerable queries, three per demo catalog product;
- 6 negative, unsupported, service-intent, or out-of-catalog queries;
- no exact text duplicates from frozen `ru-dirty-v0.1`.

Its SHA-256 is
`1d5b281a5e53851767b08c19e40e87772e8aade31c8b291db6b0d0655b71fbff`.

## Development experiment

Lexical v0.1 initially measured:

| Metric | Before |
| --- | ---: |
| Accuracy@1 | 0.667 |
| Negative accuracy | 0.833 |
| End-to-end accuracy | 0.708 |
| Accepted precision | 0.923 |
| Coverage | 0.542 |

The seven failures exposed three general problems: concatenated model strings,
phonetic/transliterated brand forms, and generic category words producing false
matches.

Lexical development v0.2 added compact comparison, conservative product-term
transliteration, and weak-category-token filtering. On the same development set it
measured:

| Metric | After |
| --- | ---: |
| Accuracy@1 | 1.000 |
| Negative accuracy | 1.000 |
| End-to-end accuracy | 1.000 |
| Accepted precision | 1.000 |
| Coverage | 0.750 |

This perfect development score is not a production claim. The set is small,
synthetic, and directly used to design the changes. It demonstrates only that the
implementation satisfies these development cases.

## Evaluation boundary

The frozen v0.1 benchmark was already inspected during baseline error analysis.
Running v0.2 on it could be useful as a regression check, but the resulting number
would not be an unbiased test estimate and is therefore not reported as a new test
result. A future comparison requires new independently written, human-reviewed
holdout queries that were not visible during implementation.

## Reproduce

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate_lexical_development.py
```

The command verifies the development dataset checksum before evaluation and writes
all predictions to `reports/development/lexical_development_v0_2.json`.
