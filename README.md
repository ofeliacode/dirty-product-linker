# Dirty Product Linker

Production-oriented product extraction and entity linking from noisy Russian, English, and transliterated text.

The project now includes its first executable milestone: versioned Pydantic data
contracts and validated sample JSONL records. See [SPEC.md](SPEC.md) for the complete
architecture and [docs/data-contract.md](docs/data-contract.md) for the implemented
catalog and annotation formats.

Planned interfaces:

- Python library
- batch CLI
- FastAPI inference service
- reproducible training and evaluation pipeline

No quality metrics are claimed before the test split is frozen and the baseline is executed.

## Current verification

Create a Python 3.12 virtual environment and install the development dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[data,dev]'
PYTHONPATH=src .venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src
```

The sample catalog is intentionally small. It validates the format and category
coverage; it is not used to claim model quality.

## Import the public catalog source

The project includes a pinned, streaming importer for the Apache-2.0 Shopify Product
Catalogue:

```bash
PYTHONPATH=src .venv/bin/python scripts/import_shopify_catalog.py --limit 1000
```

It writes a validated local JSONL catalog and an audit report without committing the
downloaded data to Git. See [docs/source-data.md](docs/source-data.md) for provenance,
limitations, and the live smoke-test result.

Build a deterministic balanced release from the imported products:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_catalog.py \
  --config configs/data/catalog_v1.yaml
```

The taxonomy, checkpoint/resume flow, deduplication, balanced selection, manifest,
and checksum process is documented in
[docs/catalog-building.md](docs/catalog-building.md). The pinned Shopify train scan
completed, but its supported output is heavily concentrated in home appliances; a
second licensed source is required before this catalog can serve as the five-category
benchmark matrix.

## Import query-product relevance judgments

Amazon ESCI is registered separately from the category catalog because it answers a
different question: how relevant is a product to a real shopping query? Import a
small, pinned, streaming sample of its training split with:

```bash
PYTHONPATH=src .venv/bin/python scripts/import_esci_queries.py --limit 1000
```

The importer preserves the ESCI label (Exact, Substitute, Complement, or Irrelevant),
locale, original IDs, source split, and source revision. The official test split is
intentionally blocked from this development-data command to prevent evaluation
leakage. ESCI has no product-category ground truth, so it is not used to fill gaps in
the five-category catalog.

## Build the Russian dirty-query benchmark

The repository includes 20 AI-authored annotation candidates covering dirty,
ambiguous, and negative queries. They are deliberately marked `synthetic` and cannot
be frozen until a person reviews or edits every row. The freeze command enforces
human provenance, catalog references, unique IDs, deterministic ordering, and
checksums. See [docs/benchmark-review.md](docs/benchmark-review.md) for the review
workflow and its boundaries.
