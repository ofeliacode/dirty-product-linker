# Lexical baseline v0.1

## Why this baseline exists

The first model is deliberately not an LLM. It establishes a cheap, deterministic,
CPU-only floor before embeddings, NER training, or reranking are introduced. Every
later approach must improve measured behavior enough to justify its complexity.

## Pipeline

```text
query
→ Unicode NFKC and case folding
→ punctuation and whitespace normalization
→ small explicit Russian product-term map
→ model/family/alias candidate surfaces
→ token F1 + character-trigram Dice score
→ fixed 0.42 acceptance threshold
→ top-5 candidates or unknown
```

The catalog brand is not indexed as a strong standalone surface. This prevents a
query such as `хочу стиралку samsung` from linking to a Samsung phone solely because
the manufacturer matches.

## Frozen evaluation

Configuration: `configs/eval/lexical_baseline_v0_1.yaml`  
Benchmark: `ru-dirty-v0.1`  
Benchmark SHA-256:
`df8473ba72bde5e19eb5e5de668836fbcfeaffb67b4e553026c5971079d02d53`

The threshold and top-k were fixed before the first benchmark run. They were not
changed after inspecting results.

| Metric | Result |
| --- | ---: |
| Answerable Accuracy@1 | 0.733 |
| Recall@5 | 1.000 |
| Negative accuracy | 1.000 |
| End-to-end accuracy | 0.800 |
| Accepted-link precision | 1.000 |
| Coverage | 0.550 |

Slice-level Accuracy@1 was 0.833 on 12 dirty queries and 0.333 on 3 ambiguous
queries. All 5 negative examples were correctly rejected.

## Error analysis

The four end-to-end errors were abstentions, not accepted wrong links:

| Query | Top candidate | Score | Failure pattern |
| --- | --- | ---: | --- |
| `нужен флагман на 256` | iPhone 15 Pro Max | 0.000 | No explicit model term |
| `телефон про макс или ультра` | iPhone 15 Pro Max | 0.361 | Partial terms from two products |
| `mbp14m3` | MacBook Pro 14 M3 | 0.106 | Fully concatenated abbreviation |
| `lgc3 55дюймов` | LG OLED C3 55 | 0.150 | Concatenated model and unit |

This baseline is conservative: accepted precision is high because coverage is low.
Lowering the threshold on this test set would be post-hoc tuning and is therefore
forbidden. Improvements need a separate development set.

## Limitations

- Twenty benchmark examples are enough to verify the pipeline, not to support a
  production-quality claim or a tight confidence interval.
- The catalog has only six products. Recall@5 is consequently weak evidence because
  five candidates cover almost the whole catalog.
- There is no span-level NER prediction yet, so exact/relaxed span F1 and category F1
  are not reported.
- The normalizer uses a small hand-written vocabulary and does not generalize to all
  brands, models, transliterations, or morphological forms.
- Latency must be benchmarked separately with warmup and repeated runs; it is not
  mixed into this deterministic quality report.

## Reproduce

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate_lexical_baseline.py
```

The full report in `reports/evaluation/lexical_baseline_v0_1.json` includes every
query, target, decision, score, matched surface, and top-k candidate list.
