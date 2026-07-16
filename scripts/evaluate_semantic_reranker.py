"""Evaluate the explainable feature-aware reranker on semantic development data."""

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
from dirty_product_linker.linking.lexical import LexicalProductLinker
from dirty_product_linker.linking.reranker import FeatureAwareReranker
from dirty_product_linker.schemas import AnnotatedQuery, Product


class RerankerConfig(BaseModel):
    """Pinned inputs and fixed policy for one reranker experiment."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    evaluation_id: str
    dataset_path: Path
    expected_dataset_sha256: str
    catalog_path: Path
    expected_catalog_sha256: str
    model_id: str
    model_revision: str
    device: str
    candidate_top_k: int = Field(ge=1)
    output_top_k: int = Field(ge=1)
    min_score: float = Field(ge=0, le=1)
    min_margin: float = Field(ge=0, le=1)
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/eval/semantic_reranker_v0_1.yaml"),
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
        config = RerankerConfig.model_validate(yaml.safe_load(source))
    dataset_bytes = config.dataset_path.read_bytes()
    catalog_bytes = config.catalog_path.read_bytes()
    dataset_sha256 = hashlib.sha256(dataset_bytes).hexdigest()
    catalog_sha256 = hashlib.sha256(catalog_bytes).hexdigest()
    if dataset_sha256 != config.expected_dataset_sha256:
        raise ValueError("development dataset checksum mismatch")
    if catalog_sha256 != config.expected_catalog_sha256:
        raise ValueError("catalog checksum mismatch")

    queries = [
        AnnotatedQuery.model_validate_json(line)
        for line in dataset_bytes.decode().splitlines()
        if line
    ]
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
    lexical = LexicalProductLinker(products, min_score=0.0)
    dense = EmbeddingProductLinker(products, encoder=encoder, min_score=-1.0)
    reranker = FeatureAwareReranker(
        products,
        min_score=config.min_score,
        min_margin=config.min_margin,
    )

    for query in queries[:3]:
        lexical_raw = lexical.link(query.text, top_k=config.candidate_top_k)
        dense_raw = dense.link(query.text, top_k=config.candidate_top_k)
        reranker.rerank(
            query.text,
            lexical=lexical_raw,
            dense=dense_raw,
            top_k=config.output_top_k,
        )

    predictions = {}
    latencies_ms: list[float] = []
    for query in queries:
        started = time.perf_counter()
        lexical_raw = lexical.link(query.text, top_k=config.candidate_top_k)
        dense_raw = dense.link(query.text, top_k=config.candidate_top_k)
        predictions[query.query_id] = reranker.rerank(
            query.text,
            lexical=lexical_raw,
            dense=dense_raw,
            top_k=config.output_top_k,
        )
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
            "candidate_top_k": config.candidate_top_k,
            "output_top_k": config.output_top_k,
            "min_score": config.min_score,
            "min_margin": config.min_margin,
            "weights": {
                "explicit_alias_boost": 0.30,
                "brand": 0.30,
                "category": 0.15,
                "model": 0.15,
                "attributes": 0.10,
                "dense": 0.20,
                "lexical": 0.10,
            },
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
        f"Accuracy@1={metrics.overall.accuracy_at_1:.3f}; "
        f"negative_accuracy={metrics.overall.negative_accuracy:.3f}; "
        f"end_to_end={metrics.overall.end_to_end_accuracy:.3f}; "
        f"precision={metrics.overall.accepted_precision:.3f}; "
        f"coverage={metrics.overall.coverage:.3f}; "
        f"p95={_percentile(latencies_ms, 0.95):.1f}ms"
    )


if __name__ == "__main__":
    main()
