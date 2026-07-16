# Spec: Dirty Product Linker

## Objective

Build a reproducible open-source ML system that extracts product mentions from noisy Russian, English, and transliterated text, classifies the product category, and links each mention to a catalog entity or product family.

The project serves three purposes:

1. Portfolio evidence for an AI/ML engineer role.
2. A reusable reference implementation for product NER and entity linking.
3. A source of benchmark data and a technical article with honest error analysis.

### Primary user stories

- As an application developer, I can submit noisy text and receive structured product entities with confidence scores.
- As an ML engineer, I can reproduce data preparation, training, evaluation, and export from versioned configuration.
- As a catalog operator, I can add new products without retraining the NER model.
- As a reviewer, I can inspect fixed splits, metrics, failure examples, latency, and model limitations.

### Output contract

```json
{
  "text": "нужен чехол на 15pm и зарядка самсунг с24 ультра",
  "entities": [
    {
      "mention": "15pm",
      "span": {"start": 15, "end": 19},
      "normalized_name": "Apple iPhone 15 Pro Max",
      "product_id": "apple-iphone-15-pro-max",
      "product_family_id": "apple-iphone-15-pro-max",
      "category": "smartphones",
      "attributes": {
        "brand": "Apple",
        "family": "iPhone",
        "model": "15 Pro Max"
      },
      "status": "linked",
      "confidence": 0.94,
      "candidates": []
    }
  ],
  "model_version": "0.1.0",
  "catalog_version": "demo-1",
  "processing_ms": 42
}
```

Supported statuses:

- `linked`: confident SKU or canonical product link.
- `family_only`: product family found, exact SKU not justified.
- `ambiguous`: multiple plausible candidates.
- `unknown`: no reliable catalog match.

## Scope

### Included in v1

- Russian, English, mixed-language, and transliterated input.
- Smartphones, laptops, headphones, televisions, and home appliances.
- Unicode and abbreviation normalization with original-offset preservation.
- Product mention and attribute extraction.
- Hybrid candidate retrieval using aliases, character n-grams, lexical search, and optional embeddings.
- Candidate reranking and calibrated abstention.
- Fixed evaluation splits including unseen SKU and dirty-text slices.
- Python library, batch CLI, FastAPI service, Docker image, tests, and documentation.
- CPU-first benchmark and optional GPU benchmark.
- Synthetic training data with documented provenance and a manually reviewed test set.

### Excluded from v1

- Crawling commercial product catalogs.
- Production-scale distributed training.
- Full multilingual support beyond Russian and English.
- Price extraction and offer matching.
- Image-based product recognition.
- A hosted SaaS or persistent customer database.
- Claims of production quality before measured evaluation.

## Architecture

```text
Raw text
  -> offset-preserving normalizer
  -> mention and attribute extractor
  -> catalog candidate generator
  -> candidate reranker
  -> category consistency check
  -> confidence calibration and abstention
  -> structured response
```

### Model strategy

The first executable baseline uses deterministic normalization, catalog aliases, character n-gram retrieval, and rule-based attribute extraction. This establishes a measurable floor before training.

The learned pipeline will compare:

1. A compact multilingual encoder for token or span classification.
2. A feature-based linker using lexical, numeric, category, and semantic signals.
3. An optional cross-encoder reranker if it provides a measurable end-to-end gain.

Generative LLMs may create candidate augmentations and weak labels, but generated examples must be tagged by provenance and may not enter the manually reviewed test set.

## Dataset Design

### Catalog record

```json
{
  "product_id": "apple-iphone-15-pro-max-256gb",
  "family_id": "apple-iphone-15-pro-max",
  "canonical_name": "Apple iPhone 15 Pro Max 256GB",
  "brand": "Apple",
  "family": "iPhone",
  "model": "15 Pro Max",
  "category": "smartphones",
  "attributes": {"storage_gb": 256},
  "aliases": ["iphone 15 pro max 256", "айфон 15 про макс 256", "15pm 256"]
}
```

### Annotation record

```json
{
  "id": "example-000001",
  "text": "хочу 15pm на 256",
  "entities": [
    {
      "start": 5,
      "end": 9,
      "type": "PRODUCT",
      "product_id": "apple-iphone-15-pro-max-256gb",
      "family_id": "apple-iphone-15-pro-max"
    }
  ],
  "source": "human-authored",
  "difficulty_tags": ["abbreviation", "lowercase"]
}
```

### Split policy

Random row splitting is forbidden. Splits are grouped by product ID and family to prevent alias leakage.

- `validation_seen`: known products, unseen phrasings.
- `test_seen`: known product families, independently written phrasings.
- `test_unseen_sku`: product IDs absent from training.
- `test_dirty`: typos, abbreviations, transliteration, mixed scripts, missing punctuation.
- `test_ambiguous`: intentionally underspecified requests.
- `test_negative`: text without a linkable product.

The test manifest, examples, thresholds, and checksum are frozen before model selection.

## Evaluation

### Required metrics

- Exact and relaxed span micro F1.
- Category macro F1.
- Entity linking Accuracy@1 and Recall@5.
- End-to-end exact entity accuracy.
- Accepted-prediction precision and overall coverage.
- Per-slice metrics for seen, unseen SKU, dirty, ambiguous, and negative data.
- p50 and p95 latency for batch sizes 1 and 16.
- Peak resident memory on the documented reference machine.

### Initial target thresholds

Targets are acceptance goals, not pre-announced results:

| Metric | Target |
|---|---:|
| Exact span F1 | >= 0.90 |
| Relaxed span F1 | >= 0.94 |
| Category macro F1 | >= 0.88 |
| Seen-SKU Accuracy@1 | >= 0.88 |
| Unseen-SKU Accuracy@1 | >= 0.72 |
| Linking Recall@5 | >= 0.95 |
| Precision for accepted links | >= 0.92 |
| Dirty-slice end-to-end accuracy | >= 0.75 |
| CPU p95, batch 1 | <= 200 ms |

If a threshold is missed, the report must include the measured result, failure clusters, and a prioritized remediation plan. Results must never be rewritten or selectively omitted to make the project appear stronger.

## Tech Stack

- Python 3.12.
- `uv` for dependency and environment management.
- Pydantic for schemas.
- scikit-learn for the deterministic and feature baselines.
- PyTorch and Transformers for the learned extractor.
- sentence-transformers only if semantic retrieval improves held-out results.
- FastAPI and Uvicorn for inference.
- Typer for the CLI.
- pytest, Ruff, and mypy for quality checks.
- Docker for reproducible serving.
- GitHub Actions for linting, tests, and a small deterministic evaluation smoke test.

Dependency versions will be pinned in `uv.lock`. Optional ML dependencies must remain separate from the lightweight runtime when practical.

## Commands

```bash
uv sync --all-extras
uv run python scripts/build_demo_catalog.py
uv run python scripts/generate_dataset.py --config configs/data/demo.yaml
uv run python scripts/freeze_splits.py --config configs/data/demo.yaml
uv run python scripts/train_baseline.py --config configs/models/baseline.yaml
uv run python scripts/train_ner.py --config configs/models/ner.yaml
uv run python scripts/evaluate.py --config configs/eval/default.yaml
uv run product-linker predict "ищу 15pm на 256"
uv run uvicorn product_linker.api.app:app --reload
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
docker build -t dirty-product-linker .
```

## Project Structure

```text
configs/                     Versioned data, model, and evaluation configs
data/                        Schemas, small public demo data, frozen manifests
docs/                        Architecture, data, evaluation, deployment, article draft
models/                      Local artifacts ignored by Git; model cards tracked
reports/                     Reproducible metrics and error-analysis outputs
scripts/                     Data, training, export, and evaluation entry points
src/product_linker/
  api/                       FastAPI application and schemas
  catalog/                   Catalog loading, indexing, and versioning
  classification/            Category classification
  evaluation/                Metrics, slices, reports, and error clustering
  linking/                   Candidate generation, reranking, calibration
  ner/                       Mention and attribute extraction
  normalization/             Offset-preserving text normalization
  pipeline.py                Public orchestration API
tests/                       Unit, integration, regression, and API tests
```

## Code Style

Public functions are typed, deterministic by default, and return explicit domain models.

```python
def link_products(
    text: str,
    *,
    catalog: ProductCatalog,
    min_confidence: float = 0.80,
) -> LinkingResult:
    """Extract and link product mentions without guessing below threshold."""
```

Rules:

- `snake_case` for functions and modules; `PascalCase` for classes.
- No hidden global model loading.
- No network access inside core inference.
- Randomness requires an explicit seed.
- Every serialized result includes model, catalog, schema, and pipeline versions.

## Testing Strategy

- Unit tests: normalization, offsets, aliases, numeric attributes, confidence policy.
- Property tests: normalization never produces invalid spans.
- Retrieval tests: required candidates appear in top-k for fixed examples.
- Integration tests: text to final structured entities.
- API contract tests: status codes and response schema.
- Regression tests: frozen difficult examples.
- Training smoke test: tiny dataset completes on CPU.
- Reproducibility test: identical inputs and artifacts produce identical outputs.

Target coverage is at least 85% for non-training application code. Model quality is verified through evaluation metrics, not line coverage.

## Production Requirements

- CPU-first inference path.
- Lazy or startup-time artifact loading, never per request.
- Batch endpoint and library API.
- Health and readiness endpoints.
- Structured logs without raw user text by default.
- Prometheus-compatible latency and status counters.
- Bounded input length and validated request size.
- Deterministic fallback when the learned model is unavailable.
- Docker image with a non-root user.

## Documentation Deliverables

- README with problem, approach, quickstart, measured results, and limitations.
- Architecture decision record comparing LLM-only and hybrid approaches.
- Dataset card with provenance and split policy.
- Model card with intended use and limitations.
- Evaluation report with full slice metrics and failures.
- CPU/GPU deployment recommendations.
- Retraining and catalog-update guides.
- Technical article draft: problem, baseline, leakage discovery, hybrid design, metrics, failures, and next steps.

## Boundaries

### Always

- Freeze test data and thresholds before model selection.
- Preserve original text offsets.
- Report all required slices.
- Pin dependencies and random seeds.
- Keep synthetic and human-authored provenance separate.
- Run tests before commits.
- Prefer measurable improvements over architectural complexity.

### Ask first

- Adding a paid API or service.
- Uploading artifacts to a public Hugging Face account.
- Changing frozen test examples or target metrics.
- Adding scraped commercial data.
- Introducing GPU-only runtime requirements.

### Never

- Commit credentials, private data, or licensed commercial catalogs.
- Train on the frozen test set.
- fabricate metrics or claim production readiness without evidence.
- silently fall back to a remote model API.
- execute model repository code without explicit review.

## Success Criteria

- A new developer can reproduce the baseline from a clean checkout.
- The repository contains a public catalog and dataset sufficient for demonstration.
- Evaluation splits prevent direct SKU and alias leakage.
- The baseline and learned approach are compared on identical frozen data.
- Metrics are reported for all required slices, including negative results.
- New catalog products can be indexed without retraining the extractor.
- Library, CLI, and API produce the same versioned schema.
- CPU latency and memory are measured on documented hardware.
- Docker, tests, linting, typing, and CI pass.
- Training, inference, evaluation, export, and retraining are documented.

## Delivery Phases

1. Data contract, catalog, split policy, and deterministic baseline.
2. Frozen evaluation harness and baseline error analysis.
3. Learned NER and dirty-text augmentation.
4. Hybrid retrieval, reranking, and confidence calibration.
5. API, CLI, Docker, profiling, and observability.
6. Documentation, Hugging Face artifacts, article, and portfolio packaging.

## Open Questions Deferred by Explicit Assumption

- No private employer dataset is available, so v1 uses a transparent synthetic/public demo dataset.
- No production traffic target is supplied, so latency is measured at batch sizes 1 and 16.
- Exact SKU linking is attempted only where attributes justify it; otherwise the system returns family-level or ambiguous results.
- Public model and dataset publication requires separate account authorization after local validation.
