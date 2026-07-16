# Source data registry and streaming imports

Third-party data is treated as a versioned input, not as an implicit dependency. The
registry at `configs/data/sources.yaml` records the dataset ID, exact revision,
license, columns, intended uses, and prohibited uses.

## Shopify Product Catalogue

The first registered source is
[`Shopify/product-catalogue`](https://huggingface.co/datasets/Shopify/product-catalogue).
Its public dataset card reports an Apache-2.0 license, 48.3k rows, train and test
splits, and the columns used by our adapter. The project pins revision
`d5c517c509f5aca99053897ef1de797d6d7e5aa5` instead of following a mutable `main`.

This source is useful for canonical product titles, brands, and taxonomy labels. It
is not entity-linking ground truth: it has no stable merchant SKU field, no noisy user
queries, and no span annotations. We therefore prohibit its use as the frozen query
test set or as proof of SKU-level linking quality.

## Install data tooling

The Hugging Face dependency is optional because schema validation and inference
should not require PyArrow or network clients.

```bash
.venv/bin/python -m pip install -e '.[data,dev]'
```

## Run a bounded import

```bash
PYTHONPATH=src .venv/bin/python scripts/import_shopify_catalog.py --limit 1000
```

The loader uses the pinned revision and `streaming=True`, then selects only the five
columns required by the adapter before iteration. This avoids downloading the entire
dataset and avoids decoding the unused image column. These behaviors follow the
official Hugging Face documentation for
[`load_dataset`](https://huggingface.co/docs/datasets/package_reference/loading_methods#datasets.load_dataset)
and
[`IterableDataset.select_columns`](https://huggingface.co/docs/datasets/package_reference/main_classes#datasets.IterableDataset.select_columns).

Generated outputs are local and ignored by Git:

```text
data/processed/shopify_catalog.jsonl
reports/data/shopify_import.json
```

The JSON report accounts for every source row using `read`, `accepted`, `rejected`,
and `rejection_reasons`. An unsupported category or missing brand is visible rather
than silently discarded.

## Live smoke-test result

On the first 200 rows of the pinned train stream, the importer read 200, accepted 4,
and rejected 196: 187 unsupported categories and 9 missing brands. All four accepted
records were home appliances. This is an integration smoke test, not a model metric
or a representative category sample; the source has a broad taxonomy while v1
intentionally accepts only five categories.

## Amazon ESCI query-product judgments

The second registered source is Amazon's official
[`Shopping Queries Dataset`](https://github.com/amazon-science/esci-data), accessed
through the Hugging Face mirror
[`milistu/amazon-esci-data`](https://huggingface.co/datasets/milistu/amazon-esci-data).
The registry records both the official origin and the exact mirror revision
`3bf15ee2b5c6483fc3b96f8656d0989bf33a18b5`.

ESCI supplies real shopping queries and query-product relevance judgments:

- `E`: exact match;
- `S`: substitute;
- `C`: complement;
- `I`: irrelevant.

This supports retrieval evaluation, relevance classification, and hard-negative
mining. It does not contain a product taxonomy, Russian queries, or NER spans, so it
cannot replace our categorized catalog or frozen Russian noisy-query test set.

Import a bounded sample from the source training split:

```bash
PYTHONPATH=src .venv/bin/python scripts/import_esci_queries.py --limit 1000
```

The command intentionally rejects a request for the source `test` split. That split
must remain isolated from training and development to prevent evaluation leakage.
The first live smoke test read and accepted 100 pinned training judgments with zero
schema rejections: 60 Exact, 22 Substitute, 1 Complement, and 17 Irrelevant; 61 were
US English and 39 Spanish. These counts only verify integration and are not claimed
to represent the full dataset distribution.
