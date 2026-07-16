# Human review checklist: multi-product v0.1

Do not run the promotion command until every box below has been checked by a person.
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

- [ ] `multi-0001` — iPhone 15 Pro Max + Sony WH-1000XM5
- [ ] `multi-0002` — Samsung Galaxy S24 Ultra + Google Pixel 8 Pro
- [ ] `multi-0003` — MacBook Pro 14 M3 + AirPods Pro 2
- [ ] `multi-0004` — Dell XPS 13 + Lenovo ThinkPad X1 Carbon
- [ ] `multi-0005` — LG OLED C3 + Sony BRAVIA 8 OLED
- [ ] `multi-0006` — Samsung WW90 + Bosch KGN39
- [ ] `multi-0007` — Dyson V15 + Roborock S8 MaxV Ultra
- [ ] `multi-0008` — Bose QuietComfort Ultra + Sennheiser Momentum 4
- [ ] `multi-0009` — TCL C855 + Samsung QN90D
- [ ] `multi-0010` — OnePlus 12 + ASUS ROG Zephyrus G14

### Long context

- [ ] `context-0001` — `15pm`
- [ ] `context-0002` — `наушники xm5`
- [ ] `context-0003` — `зефирка g14`
- [ ] `context-0004` — `бравия олед`
- [ ] `context-0005` — `беспроводной дайсон`

### Unseen surfaces

- [ ] `unseen-0001` — unseen iPhone wording
- [ ] `unseen-0002` — unseen Samsung wording
- [ ] `unseen-0003` — unseen Sony wording
- [ ] `unseen-0004` — unseen MacBook wording
- [ ] `unseen-0005` — unseen Roborock wording

### Negatives

- [ ] `negative-0001` — generic phone and headphones request
- [ ] `negative-0002` — generic cleaning request
- [ ] `negative-0003` — generic laptop request
- [ ] `negative-0004` — generic television request
- [ ] `negative-0005` — no purchase intent

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
