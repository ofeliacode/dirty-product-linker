"""Benchmark pinned dense retrieval on the synthetic development set."""

import argparse
import hashlib
import json
import platform
import resource
import statistics
import time
from dataclasses import asdict
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dirty_product_linker.evaluation.baseline import (
    BenchmarkExample,
    evaluate_predictions,
)
from dirty_product_linker.evaluation.thresholds import select_threshold
from dirty_product_linker.linking.embedding import (
    EmbeddingProductLinker,
    SentenceTransformerEncoder,
)
from dirty_product_linker.linking.lexical import LexicalProductLinker
from dirty_product_linker.schemas import AnnotatedQuery, Product


class EmbeddingDevelopmentConfig(BaseModel):
    """Pinned model, data, threshold grid, and benchmark settings."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    evaluation_id: str
    dataset_path: Path
    expected_dataset_sha256: str
    catalog_path: Path
    model_id: str
    model_revision: str
    model_license: str
    embedding_dimensions: int = Field(ge=1)
    primary_weight_bytes: int = Field(ge=1)
    device: str
    top_k: int = Field(ge=1)
    warmup_queries: int = Field(ge=0)
    thresholds: list[float]
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/eval/embedding_development_v0_1.yaml"),
    )
    return parser.parse_args()


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _peak_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if platform.system() == "Darwin" else peak * 1024)


def main() -> None:
    args = parse_args()
    with args.config.open(encoding="utf-8") as source:
        config = EmbeddingDevelopmentConfig.model_validate(yaml.safe_load(source))

    dataset_bytes = config.dataset_path.read_bytes()
    dataset_sha256 = hashlib.sha256(dataset_bytes).hexdigest()
    if dataset_sha256 != config.expected_dataset_sha256:
        raise ValueError(
            "development dataset checksum mismatch: "
            f"expected {config.expected_dataset_sha256}, got {dataset_sha256}"
        )
    queries = [
        AnnotatedQuery.model_validate_json(line)
        for line in dataset_bytes.decode().splitlines()
        if line
    ]
    with config.catalog_path.open(encoding="utf-8") as source:
        products = [Product.model_validate_json(line) for line in source if line.strip()]
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

    index_started = time.perf_counter()
    linker = EmbeddingProductLinker(products, encoder=encoder, min_score=-1.0)
    catalog_index_ms = (time.perf_counter() - index_started) * 1000

    for query in queries[: config.warmup_queries]:
        linker.link(query.text, top_k=config.top_k)

    raw_predictions = {}
    latencies_ms: list[float] = []
    for query in queries:
        started = time.perf_counter()
        raw_predictions[query.query_id] = linker.link(query.text, top_k=config.top_k)
        latencies_ms.append((time.perf_counter() - started) * 1000)

    selection = select_threshold(
        examples,
        raw_predictions,
        thresholds=config.thresholds,
    )
    selected_metrics = selection.report

    lexical_linker = LexicalProductLinker(products, min_score=0.42)
    for query in queries[: config.warmup_queries]:
        lexical_linker.link(query.text, top_k=config.top_k)
    lexical_predictions = {}
    lexical_latencies_ms: list[float] = []
    for query in queries:
        started = time.perf_counter()
        lexical_predictions[query.query_id] = lexical_linker.link(
            query.text, top_k=config.top_k
        )
        lexical_latencies_ms.append((time.perf_counter() - started) * 1000)
    lexical_metrics = evaluate_predictions(examples, lexical_predictions)
    threshold_metrics = {
        str(threshold): asdict(
            evaluate_predictions(
                examples,
                select_threshold(
                    examples,
                    raw_predictions,
                    thresholds=[threshold],
                ).predictions,
            ).overall
        )
        for threshold in config.thresholds
    }
    report = {
        "schema_version": "1.0",
        "evaluation_id": config.evaluation_id,
        "dataset_role": "synthetic_development",
        "dataset_sha256": dataset_sha256,
        "model": {
            "id": config.model_id,
            "revision": config.model_revision,
            "license": config.model_license,
            "embedding_dimensions": config.embedding_dimensions,
            "primary_weight_bytes": config.primary_weight_bytes,
            "device": config.device,
        },
        "selection": {
            "rule": "end_to_end, accepted_precision, coverage, higher_threshold",
            "threshold": selection.threshold,
            "threshold_metrics": threshold_metrics,
        },
        "metrics": asdict(selected_metrics),
        "performance": {
            "model_load_ms": model_load_ms,
            "catalog_index_ms": catalog_index_ms,
            "query_latency_ms": {
                "count": len(latencies_ms),
                "mean": statistics.fmean(latencies_ms),
                "p50": _percentile(latencies_ms, 0.50),
                "p95": _percentile(latencies_ms, 0.95),
            },
            "peak_rss_bytes": _peak_rss_bytes(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "lexical_comparison": {
            "settings": {"min_score": 0.42, "top_k": config.top_k},
            "metrics": asdict(lexical_metrics),
            "query_latency_ms": {
                "count": len(lexical_latencies_ms),
                "mean": statistics.fmean(lexical_latencies_ms),
                "p50": _percentile(lexical_latencies_ms, 0.50),
                "p95": _percentile(lexical_latencies_ms, 0.95),
            },
        },
        "predictions": [
            {
                "query_id": query.query_id,
                "text": query.text,
                "target_product_ids": query.target_product_ids,
                **asdict(selection.predictions[query.query_id]),
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

    overall = selected_metrics.overall
    print(
        f"threshold={selection.threshold:.2f}; Accuracy@1={overall.accuracy_at_1:.3f}; "
        f"negative_accuracy={overall.negative_accuracy:.3f}; "
        f"end_to_end={overall.end_to_end_accuracy:.3f}; "
        f"p50={_percentile(latencies_ms, 0.50):.1f}ms; "
        f"p95={_percentile(latencies_ms, 0.95):.1f}ms"
    )


if __name__ == "__main__":
    main()
