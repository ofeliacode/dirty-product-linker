"""Benchmark lexical-first retrieval with a guarded dense fallback."""

import argparse
import hashlib
import json
import statistics
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dirty_product_linker.evaluation.baseline import (
    BenchmarkExample,
    evaluate_predictions,
)
from dirty_product_linker.linking.embedding import (
    EmbeddingProductLinker,
    SentenceTransformerEncoder,
)
from dirty_product_linker.linking.hybrid import HybridProductLinker
from dirty_product_linker.linking.lexical import LexicalProductLinker
from dirty_product_linker.schemas import AnnotatedQuery, Product


class HybridDevelopmentConfig(BaseModel):
    """Pinned hybrid policy and development inputs."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    evaluation_id: str
    dataset_path: Path
    expected_dataset_sha256: str
    catalog_path: Path
    expected_catalog_sha256: str | None = None
    model_id: str
    model_revision: str
    device: str
    top_k: int = Field(ge=1)
    lexical_min_score: float = Field(ge=0, le=1)
    dense_min_score: float = Field(ge=-1, le=1)
    dense_min_margin: float = Field(ge=0, le=2)
    lexical_support_score: float = Field(ge=0, le=1)
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/eval/hybrid_development_v0_1.yaml"),
    )
    return parser.parse_args()


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def main() -> None:
    args = parse_args()
    with args.config.open(encoding="utf-8") as source:
        config = HybridDevelopmentConfig.model_validate(yaml.safe_load(source))
    dataset_bytes = config.dataset_path.read_bytes()
    dataset_sha256 = hashlib.sha256(dataset_bytes).hexdigest()
    if dataset_sha256 != config.expected_dataset_sha256:
        raise ValueError("development dataset checksum mismatch")
    queries = [
        AnnotatedQuery.model_validate_json(line)
        for line in dataset_bytes.decode().splitlines()
        if line
    ]
    catalog_bytes = config.catalog_path.read_bytes()
    catalog_sha256 = hashlib.sha256(catalog_bytes).hexdigest()
    if (
        config.expected_catalog_sha256 is not None
        and catalog_sha256 != config.expected_catalog_sha256
    ):
        raise ValueError("catalog checksum mismatch")
    products = [
        Product.model_validate_json(line)
        for line in catalog_bytes.decode().splitlines()
        if line
    ]
    examples = [
        BenchmarkExample(
            slice_name="answerable" if query.answerable else "negative",
            query=query,
        )
        for query in queries
    ]

    load_started = time.perf_counter()
    encoder = SentenceTransformerEncoder(
        model_id=config.model_id,
        revision=config.model_revision,
        device=config.device,
    )
    model_load_ms = (time.perf_counter() - load_started) * 1000
    dense = EmbeddingProductLinker(products, encoder=encoder, min_score=-1.0)
    lexical = LexicalProductLinker(products, min_score=config.lexical_min_score)
    hybrid = HybridProductLinker(
        lexical=lexical,
        dense=dense,
        dense_min_score=config.dense_min_score,
        dense_min_margin=config.dense_min_margin,
        lexical_support_score=config.lexical_support_score,
    )

    for query in [*queries[:2], queries[-1]]:
        hybrid.link(query.text, top_k=config.top_k)

    predictions = {}
    latencies_ms: list[float] = []
    for query in queries:
        started = time.perf_counter()
        predictions[query.query_id] = hybrid.link(query.text, top_k=config.top_k)
        latencies_ms.append((time.perf_counter() - started) * 1000)
    metrics = evaluate_predictions(examples, predictions)
    source_counts = Counter(
        prediction.decision_source for prediction in predictions.values()
    )
    report = {
        "schema_version": "1.0",
        "evaluation_id": config.evaluation_id,
        "dataset_role": "synthetic_development",
        "dataset_sha256": dataset_sha256,
        "catalog_sha256": catalog_sha256,
        "model": {"id": config.model_id, "revision": config.model_revision},
        "policy": {
            "lexical_min_score": config.lexical_min_score,
            "dense_min_score": config.dense_min_score,
            "dense_min_margin": config.dense_min_margin,
            "lexical_support_score": config.lexical_support_score,
        },
        "metrics": asdict(metrics),
        "decision_source_counts": dict(sorted(source_counts.items())),
        "performance": {
            "model_load_ms": model_load_ms,
            "query_latency_ms": {
                "count": len(latencies_ms),
                "mean": statistics.fmean(latencies_ms),
                "p50": _percentile(latencies_ms, 0.50),
                "p95": _percentile(latencies_ms, 0.95),
            },
        },
        "predictions": [
            {
                "query_id": query.query_id,
                "text": query.text,
                "target_product_ids": query.target_product_ids,
                **asdict(predictions[query.query_id]),
            }
            for query in queries
        ],
    }
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = config.output_path.with_name(f".{config.output_path.name}.tmp")
    temporary_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(config.output_path)

    print(
        f"end_to_end={metrics.overall.end_to_end_accuracy:.3f}; "
        f"sources={dict(sorted(source_counts.items()))}; "
        f"p50={_percentile(latencies_ms, 0.50):.2f}ms; "
        f"p95={_percentile(latencies_ms, 0.95):.2f}ms"
    )


if __name__ == "__main__":
    main()
