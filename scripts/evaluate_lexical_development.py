"""Evaluate the lexical linker on the checksum-pinned synthetic development set."""

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


class DevelopmentConfig(BaseModel):
    """Pinned development inputs and linker decision settings."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    evaluation_id: str
    dataset_path: Path
    expected_dataset_sha256: str
    catalog_path: Path
    min_score: float = Field(ge=0, le=1)
    top_k: int = Field(ge=1)
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/eval/lexical_development_v0_2.yaml"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.config.open(encoding="utf-8") as source:
        config = DevelopmentConfig.model_validate(yaml.safe_load(source))

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
    linker = LexicalProductLinker(products, min_score=config.min_score)
    predictions = {
        query.query_id: linker.link(query.text, top_k=config.top_k)
        for query in queries
    }
    metrics = evaluate_predictions(examples, predictions)
    report = {
        "schema_version": "1.0",
        "evaluation_id": config.evaluation_id,
        "dataset_role": "synthetic_development",
        "dataset_sha256": dataset_sha256,
        "settings": {"min_score": config.min_score, "top_k": config.top_k},
        "metrics": asdict(metrics),
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

    overall = metrics.overall
    print(
        f"Development Accuracy@1={overall.accuracy_at_1:.3f}; "
        f"negative_accuracy={overall.negative_accuracy:.3f}; "
        f"end_to_end={overall.end_to_end_accuracy:.3f}; "
        f"coverage={overall.coverage:.3f}"
    )


if __name__ == "__main__":
    main()
