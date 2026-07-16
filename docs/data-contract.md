# Data contract v1

The first data contract separates the product catalog from user language.
Catalog records describe canonical products. Annotated queries describe how people
refer to those products in noisy text. Both formats use JSON Lines (`.jsonl`), with
one independently parseable JSON object per line.

## Catalog records

`data/catalog/sample_catalog.jsonl` contains small, reviewable examples. A catalog
record has the following fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Version of this serialized contract. Currently `1.0`. |
| `product_id` | Stable lowercase identifier used by the linker. |
| `category` | One of the five categories supported by the first benchmark. |
| `brand` | Canonical manufacturer name. |
| `family` | Optional product family such as `iPhone` or `Galaxy S`. |
| `model` | Canonical model name. |
| `attributes` | Typed SKU properties such as storage, color, or screen size. |
| `aliases` | Known surface forms used for retrieval, never a replacement for test data. |

The initial categories are `smartphone`, `laptop`, `headphones`, `television`, and
`home_appliance`. Adding a category is a deliberate schema change because evaluation
reports compare quality by category.

## Annotated queries

`data/examples/annotated_queries.jsonl` contains examples of noisy user language.

| Field | Meaning |
| --- | --- |
| `query_id` | Stable identifier for the annotation. |
| `text` | Original text. It must never be normalized in place. |
| `language` | Descriptive language tag such as `ru` or `ru-mixed`. |
| `noise_types` | Labels such as abbreviation, typo, or mixed script. |
| `entities` | Character spans and their normalized meanings. |
| `target_product_ids` | Gold catalog links. Empty when the query is not answerable. |
| `answerable` | Whether the available catalog contains a justified answer. |
| `provenance` | `human`, `public_dataset`, or `synthetic`. |

Entity offsets use Python's half-open interval convention: `text[start:end]`. The
substring must exactly equal the entity's `text` field. This preserves the original
user input and makes NER evaluation deterministic.

## Validation rules

Pydantic models in `src/dirty_product_linker/schemas.py` enforce the contract:

- identifiers are lowercase slugs;
- required strings cannot be empty;
- unknown fields are rejected instead of silently ignored;
- entity offsets must be ordered and match the source text;
- an unanswerable query cannot name a target product;
- every public example is checked by the test suite;
- every target in the sample queries must exist in the sample catalog.

Run the checks locally with:

```bash
PYTHONPATH=src .venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src
```

## What this sample is not

The sample files are contract fixtures, not training or evaluation datasets. They are
too small to support quality claims. Dataset import, license manifests, grouped split
generation, and a manually reviewed frozen test set are separate later milestones.

