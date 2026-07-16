"""Evaluate the fixed lexical baseline on a checksum-verified benchmark."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dirty_product_linker.evaluation.baseline import (
    BenchmarkExample,
    evaluate_predictions,
)
from dirty_product_linker.linking.lexical import LexicalProductLinker
from dirty_product_linker.schemas import AnnotatedQuery, Product


class EvaluationConfig(BaseModel):
    """Pinned inputs and fixed decision settings for one baseline run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    evaluation_id: str
    benchmark_version: str
    benchmark_path: Path
    benchmark_manifest_path: Path
    expected_benchmark_sha256: str
    catalog_path: Path
    min_score: float = Field(ge=0, le=1)
    top_k: int = Field(ge=1)
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/eval/lexical_baseline_v0_1.yaml"),
    )
    return parser.parse_args()


def _load_config(path: Path) -> EvaluationConfig:
    with path.open(encoding="utf-8") as source:
        return EvaluationConfig.model_validate(yaml.safe_load(source))


def _load_catalog(path: Path) -> list[Product]:
    with path.open(encoding="utf-8") as source:
        return [Product.model_validate_json(line) for line in source if line.strip()]


def _load_benchmark(path: Path) -> list[BenchmarkExample]:
    examples: list[BenchmarkExample] = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            slice_name = row.pop("slice")
            examples.append(
                BenchmarkExample(
                    slice_name=slice_name,
                    query=AnnotatedQuery.model_validate(row),
                )
            )
    return examples


def main() -> None:
    args = parse_args()
    config = _load_config(args.config)
    benchmark_bytes = config.benchmark_path.read_bytes()
    actual_sha256 = hashlib.sha256(benchmark_bytes).hexdigest()
    if actual_sha256 != config.expected_benchmark_sha256:
        raise ValueError(
            "benchmark checksum mismatch: "
            f"expected {config.expected_benchmark_sha256}, got {actual_sha256}"
        )

    examples = _load_benchmark(config.benchmark_path)
    linker = LexicalProductLinker(
        _load_catalog(config.catalog_path),
        min_score=config.min_score,
    )
    predictions = {
        example.query.query_id: linker.link(example.query.text, top_k=config.top_k)
        for example in examples
    }
    metrics = evaluate_predictions(examples, predictions)
    benchmark_manifest = json.loads(
        config.benchmark_manifest_path.read_text(encoding="utf-8")
    )
    report = {
        "schema_version": "1.0",
        "evaluation_id": config.evaluation_id,
        "benchmark_version": config.benchmark_version,
        "benchmark_sha256": actual_sha256,
        "catalog_product_ids_sha256": benchmark_manifest[
            "catalog_product_ids_sha256"
        ],
        "settings": {"min_score": config.min_score, "top_k": config.top_k},
        "metrics": asdict(metrics),
        "predictions": [
            {
                "query_id": example.query.query_id,
                "slice": example.slice_name,
                "text": example.query.text,
                "target_product_ids": example.query.target_product_ids,
                **asdict(predictions[example.query.query_id]),
            }
            for example in examples
        ],
    }
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = config.output_path.with_name(f".{config.output_path.name}.tmp")
    temporary_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(config.output_path)

    overall = metrics.overall
    print(
        f"Accuracy@1={overall.accuracy_at_1:.3f}; "
        f"Recall@5={overall.recall_at_5:.3f}; "
        f"negative_accuracy={overall.negative_accuracy:.3f}; "
        f"end_to_end={overall.end_to_end_accuracy:.3f}; "
        f"coverage={overall.coverage:.3f}"
    )


if __name__ == "__main__":
    main()
