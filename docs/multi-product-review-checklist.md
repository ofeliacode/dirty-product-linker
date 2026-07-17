# Human review checklist: multi-product v0.1

Review completed by `ofeliacode` on `2026-07-16`. Frozen dataset SHA-256:
`9f8add6cb98028ac1449d278ed9f3bc2c6f9bfc4fc037ccaca5c703b154b2443`.
The source file is
`data/benchmark/candidates/multi_product_v0_1.jsonl`.

## What to verify for every row

1. The message sounds like something a shopper could plausibly write.
2. Every concrete product mention is annotated; generic category words are not.
3. `text[start:end]` exactly equals the annotated mention text.
4. The `product_id` is the intended catalog record.
5. A negative row contains no identifiable catalog product.
6. Unseen wording does not accidentally duplicate an existing catalog alias.

## Row checklist

### Explicit aliases

- [x] `multi-0001` — iPhone 15 Pro Max + Sony WH-1000XM5
- [x] `multi-0002` — Samsung Galaxy S24 Ultra + Google Pixel 8 Pro
- [x] `multi-0003` — MacBook Pro 14 M3 + AirPods Pro 2
- [x] `multi-0004` — Dell XPS 13 + Lenovo ThinkPad X1 Carbon
- [x] `multi-0005` — LG OLED C3 + Sony BRAVIA 8 OLED
- [x] `multi-0006` — Samsung WW90 + Bosch KGN39
- [x] `multi-0007` — Dyson V15 + Roborock S8 MaxV Ultra
- [x] `multi-0008` — Bose QuietComfort Ultra + Sennheiser Momentum 4
- [x] `multi-0009` — TCL C855 + Samsung QN90D
- [x] `multi-0010` — OnePlus 12 + ASUS ROG Zephyrus G14

### Long context

- [x] `context-0001` — `15pm`
- [x] `context-0002` — `наушники xm5`
- [x] `context-0003` — `зефирка g14`
- [x] `context-0004` — `бравия олед`
- [x] `context-0005` — `беспроводной дайсон`

### Unseen surfaces

- [x] `unseen-0001` — unseen iPhone wording
- [x] `unseen-0002` — unseen Samsung wording
- [x] `unseen-0003` — unseen Sony wording
- [x] `unseen-0004` — unseen MacBook wording
- [x] `unseen-0005` — unseen Roborock wording

### Negatives

- [x] `negative-0001` — generic phone and headphones request
- [x] `negative-0002` — generic cleaning request
- [x] `negative-0003` — generic laptop request
- [x] `negative-0004` — generic television request
- [x] `negative-0005` — no purchase intent

## Freeze after review

Correct the candidate JSONL first if any row fails review. Then run:

```bash
.venv/bin/python scripts/promote_multi_product_holdout.py \
  --reviewer ofeliacode \
  --reviewed-at YYYY-MM-DD \
  --confirm-all
```

The command creates:

- `data/benchmark/frozen/multi_product_v0_1.jsonl` with provenance `human`;
- `data/benchmark/frozen/multi_product_v0_1_manifest.json` with reviewer,
  timestamp, slice counts, attestation, and SHA-256 checksums.

Promotion is deliberately one-way: the command refuses to overwrite either frozen
file. If the candidate set changes after review, create a new benchmark version.
