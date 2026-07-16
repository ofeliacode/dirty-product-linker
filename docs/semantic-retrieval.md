# Catalog v0.2 and semantic retrieval experiment

## Why the catalog changed

The original six-product catalog made retrieval metrics artificially easy: most
categories contained only one candidate, and Recall@5 covered almost the entire
catalog. `demo_catalog_v0_2.jsonl` is a separate version with 20 products, balanced
at four products per category.

The original six products remain unchanged. The v0.2 SHA-256 is
`9ba193ce8098b411febd3ff9d55a2c30210580aa8adf8e7d92b6ae0e345c6526`.
Names and model identifiers are manually curated demo facts; aliases and attributes
are development metadata, not claimed retailer ground truth.

## Semantic development slice

`semantic_dev_v0_1.jsonl` contains 25 synthetic development queries:

- 20 answerable descriptions without an exact model or catalog alias;
- 5 intentionally underspecified negative queries;
- no exact text overlap with the earlier development or frozen benchmark files.

Examples include descriptions such as a Samsung flagship with a stylus, a Lenovo
business laptop made of carbon, and an underspecified request for any 55-inch TV.
The dataset SHA-256 is
`fb4e95e9527dd636f233d69d0435992ae5d51fd272ed470af505454d9d217ffc`.

## Results

| Method | Accuracy@1 | Recall@5 | Negative accuracy | End-to-end | Accepted precision | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical v0.2 | 0.100 | 1.000 | 0.800 | 0.240 | 0.667 | 0.120 |
| Dense MiniLM | 0.550 | 0.900 | 0.400 | 0.520 | 0.611 | 0.720 |
| Guarded hybrid | 0.150 | 1.000 | 0.800 | 0.280 | 0.750 | 0.160 |

Dense retrieval is materially better than lexical on semantic descriptions, but its
precision is too low for trustworthy model-level linking. It incorrectly accepted
generic requests for a work laptop, a 55-inch TV, and wireless headphones. It also
confused nearby products within a category.

The previously fixed hybrid policy made 18 lexical decisions on the old identifier
development slice, but only 3 on this semantic slice. It accepted one correct dense
fallback (`белая стиральная машина samsung на девять килограмм`) and abstained on 21
queries. This preserved more precision but sacrificed most coverage.

## Interpretation

The expanded matrix changes the conclusion:

- lexical retrieval is excellent for explicit identifiers and aliases;
- embeddings improve recall for descriptive language;
- dense similarity alone confuses brand, category, and exact model identity;
- strict agreement guards protect precision but block too many useful recoveries.

The next justified component is a feature-aware reranker, not another embedding
model. Candidate features should include exact/normalized brand evidence, category
compatibility, model-token evidence, attribute agreement, dense score, lexical score,
and top-two margin. It should be trained or calibrated only on development data.

No frozen-test metric is reported for these experiments.

## Reproduce

```bash
HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python \
  scripts/evaluate_embedding_development.py \
  --config configs/eval/semantic_embedding_v0_1.yaml

HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python \
  scripts/evaluate_hybrid_development.py \
  --config configs/eval/semantic_hybrid_v0_1.yaml
```
