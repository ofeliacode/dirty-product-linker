# Hybrid linker v0.1

## Policy

The hybrid experiment is lexical-first and invokes dense retrieval only after a
lexical abstention. Dense scores are never averaged with lexical scores because the
two values are not calibrated to the same probability scale.

Dense fallback requires all of the following:

- dense cosine score at least `0.65`;
- top-1 versus top-2 dense margin at least `0.12`;
- weak lexical support at least `0.15`;
- lexical and dense top-1 product IDs agree.

If lexical already returns `linked`, the model is not invoked for that query. A
conflicting dense result can therefore never overwrite a confident exact identifier.

## Development result

On the 24-query synthetic development set:

| Metric | Hybrid v0.1 |
| --- | ---: |
| Accuracy@1 | 1.000 |
| Negative accuracy | 1.000 |
| End-to-end accuracy | 1.000 |
| Accepted precision | 1.000 |
| Coverage | 0.750 |

Decision paths:

- `lexical`: 18;
- `dense_fallback`: 0;
- `abstain`: 6.

Hybrid preserved the lexical result, but dense retrieval recovered no additional
development query. It only verified six lexical abstentions.

## Selective-inference performance

After warmup on the local Apple arm64 CPU:

- p50 end-to-end query latency: approximately `0.17 ms`;
- p95 end-to-end query latency: approximately `17.63 ms`;
- mean: approximately `4.52 ms`;
- model loading: approximately `7.36 s`.

The median stays close to lexical because 75% of queries exit before dense inference.
Tail latency reflects the six queries that invoke MiniLM.

## Decision

Lexical v0.2 remains the default runtime. Dense fallback is disabled by default
because it adds model download size, memory, startup time, and tail latency without a
demonstrated recovery benefit on the current development data.

The hybrid path remains useful as tested experimental infrastructure. It should be
reconsidered only after adding a separate semantic development slice where:

- the correct product is not recoverable from identifiers or aliases;
- natural-language intent still uniquely identifies a catalog item;
- dense fallback improves coverage without reducing accepted precision.

No frozen-test result is claimed for hybrid v0.1.

## Reproduce

```bash
HF_HUB_OFFLINE=1 PYTHONPATH=src .venv/bin/python \
  scripts/evaluate_hybrid_development.py
```
