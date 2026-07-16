# Building catalog v1

Catalog construction is split into two commands so network ingestion and local
release selection can be inspected independently.

## 1. Import supported Shopify records

```bash
PYTHONPATH=src .venv/bin/python scripts/import_shopify_catalog.py \
  --limit 50000 \
  --checkpoint-every 1000 \
  --taxonomy configs/data/taxonomy.yaml
```

The taxonomy configuration uses exact paths for devices and explicitly approved
subtrees for appliances. Broad substring rules are forbidden: phone cases, laptop
bags, and TV mounts must not be classified as devices.

The importer atomically saves cumulative state to
`reports/data/shopify_import_checkpoint.json`. If the network or process stops,
continue without discarding confirmed rows:

```bash
PYTHONPATH=src .venv/bin/python scripts/import_shopify_catalog.py \
  --limit 50000 \
  --checkpoint-every 1000 \
  --resume
```

The checkpoint includes the pinned dataset identity, processed-row count, accepted
products, and rejection counters. A checkpoint from another revision or split is
rejected. Until a full scan completes, a small smoke-test catalog must not be
described as `catalog-v1` evaluation data.

## 2. Build a deterministic release

```bash
PYTHONPATH=src .venv/bin/python scripts/build_catalog.py \
  --config configs/data/catalog_v1.yaml
```

The builder:

1. validates every imported JSONL row as a `Product`;
2. removes conservative duplicates by normalized category, brand, and model;
3. ranks products using SHA-256 of `seed:product_id`;
4. keeps at most the configured number from each category;
5. writes byte-stable JSONL;
6. writes a manifest with counts, source revision, seed, and SHA-256 checksum.

Different storage values remain distinct because they remain part of the normalized
model text. The same source, configuration, and seed produce a byte-identical catalog.

## Current status

The resumable import completed the pinned Shopify train split with the following
observed counts:

```text
source rows:          43,111
accepted:                700
missing brand:           786
unsupported category: 41,625
duplicates removed:       82
catalog output:           506
```

The deterministic release contains 500 home appliances, 3 laptops, and 3
televisions. It contains no smartphones or headphones under the current exact
taxonomy mapping. This is a source-coverage result, not model quality. We will add a
second licensed source for missing consumer-electronics categories instead of
loosening taxonomy rules until accessories become false device matches.

The generated catalog checksum is
`c3f4b195ff3bba3e06fe5952efa55f1e8284723147e709d3ad6ae59e5b3247c9`.
Generated JSONL, reports, and checkpoints remain local and ignored by Git.
