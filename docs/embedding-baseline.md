# Multilingual embedding retrieval baseline

## Experiment

The dense baseline uses
[`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
at immutable revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`.
The Apache-2.0 model maps text to 384-dimensional vectors and has an approximately
471 MB primary safetensors weight file.

Each catalog product becomes one document containing its brand, family, model,
category, aliases, and attributes. Catalog vectors are computed once. Query vectors
are compared with cosine similarity.

The threshold was selected only on the checksum-pinned synthetic development set.
The deterministic selection objective was:

1. maximum end-to-end accuracy;
2. maximum accepted precision;
3. maximum coverage;
4. higher threshold as a conservative final tie-break.

The selected threshold was `0.40` from the predeclared grid `0.20–0.80`.

## Development results

| Metric | Dense MiniLM | Lexical v0.2 |
| --- | ---: | ---: |
| Accuracy@1 | 0.889 | 1.000 |
| Recall@5 | 1.000 | 1.000 |
| Negative accuracy | 0.667 | 1.000 |
| End-to-end accuracy | 0.833 | 1.000 |
| Accepted precision | 0.800 | 1.000 |
| Coverage | 0.833 | 0.750 |

Dense retrieval accepted more queries, but two of the additional accepted decisions
were wrong. Its four errors were:

- `самсунгс24у серый` linked to Bosch KGN39VL25R;
- `apple ноут m3 четырнадцать` linked to iPhone 15 Pro Max;
- `зарядка usb c 65w` linked to LG OLED C3;
- `наушники airpods pro 2` linked to Sony WH-1000XM5.

This shows that general semantic proximity can hurt exact catalog linking. Shared
brand or category meaning is not sufficient evidence for a model-level link.

## CPU performance

Measured locally on the documented Apple arm64 environment after three warmup
queries:

| Measurement | Dense MiniLM | Lexical v0.2 |
| --- | ---: | ---: |
| Query p50 | 15.869 ms | 0.158 ms |
| Query p95 | 17.868 ms | 0.194 ms |
| Model load | approximately 6.5 s | none |
| Catalog indexing, 6 products | approximately 0.2 s | negligible |
| Peak process RSS | approximately 1.2 GB | included in dense process |
| Primary model weight | 470,641,600 bytes | none |

Timing varies by run and hardware. Quality metrics and predictions are deterministic;
latency fields are measurements, not byte-stable artifacts.

## Decision

Dense-only retrieval does not replace lexical v0.2 in this project. The next useful
experiment is hybrid candidate generation:

- lexical identifiers provide precision for brands and models;
- dense similarity may recover natural-language paraphrases;
- explicit brand/model conflicts and confidence margins guard against semantic false
  positives.

No new frozen-test score is claimed. Both methods were compared only on the synthetic
development set used during implementation.

## Reproduce

```bash
.venv/bin/python -m pip install -e '.[embeddings]'
HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python \
  scripts/evaluate_embedding_development.py
```

The first run without `HF_HUB_OFFLINE=1` downloads the pinned model. Later runs can
use the local Hugging Face cache without network access.
