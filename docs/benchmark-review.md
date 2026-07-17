# Russian dirty-query benchmark workflow

## Objective

Create a small, auditable evaluation set for Russian, mixed-script, abbreviated,
ambiguous, and out-of-catalog product queries. The benchmark measures model quality;
it is never training data.

## Data states

```text
data/benchmark/candidates/  Synthetic proposals; provenance=synthetic
data/benchmark/reviewed/    Human-accepted or human-edited rows; provenance=human
data/benchmark/frozen/      Deterministic JSONL plus checksum manifest
```

Moving a row between these states is a review decision, not a file-copy operation.
The reviewer must read the original text, entity spans, normalized values, target
products, answerability, and slice assignment. Rejected or uncertain rows stay out.

## Initial candidate pool

The first pool contains 20 schema-valid proposals:

| Slice | Count | Purpose |
| --- | ---: | --- |
| `dirty` | 12 | Abbreviations, misspellings, mixed scripts, split/merged words |
| `ambiguous` | 3 | More than one catalog product is a justified candidate |
| `negative` | 5 | No product request, unsupported category, or out-of-catalog product |

The initial pool was reviewed by `ofeliacode` on 2026-07-16 and frozen as
`ru-dirty-v0.1`. It remains a workflow seed, not enough data for credible final model
metrics. Independent human-authored examples should expand every slice in a new
benchmark version.

## Review checklist

For every candidate:

1. Would a real user plausibly write this query?
2. Does every `text[start:end]` exactly equal the annotated entity text?
3. Is the normalized value justified by the visible text?
4. Are all and only justified catalog targets included?
5. Is `answerable=false` used when the demo catalog cannot provide a reliable link?
6. Is the slice correct?
7. Has the wording been independently edited where it sounds AI-generated?

Only after those checks may `provenance` change from `synthetic` to `human`.

## Freeze command

Once reviewed JSONL files exist, run:

```bash
PYTHONPATH=src .venv/bin/python scripts/freeze_benchmark.py
```

The command rejects synthetic rows, duplicate query IDs, and unknown target product
IDs. It writes rows in deterministic order and records both the benchmark SHA-256 and
a checksum of the catalog product-ID set. The checksum makes later benchmark or
catalog drift visible.

The frozen v0.1 release contains 20 examples and has benchmark SHA-256
`df8473ba72bde5e19eb5e5de668836fbcfeaffb67b4e553026c5971079d02d53`.
The review manifest retains the reviewer, review date, candidate checksum, and
reviewed-data checksum.

## Testing and boundaries

```bash
PYTHONPATH=src .venv/bin/pytest
PYTHONPATH=src .venv/bin/ruff check src tests scripts
PYTHONPATH=src .venv/bin/mypy src
```

- Never train on files under `data/benchmark/frozen/`.
- Never label synthetic, unreviewed text as human provenance.
- Never edit a frozen release in place; create a new benchmark version.
- Do not claim quality from the 20-row candidate pool.
