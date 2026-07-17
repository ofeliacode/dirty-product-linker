"""Evaluate rule-based multi-product extraction on pinned candidate data."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from dirty_product_linker.api.service import LexicalLinkingService
from dirty_product_linker.evaluation.mentions import evaluate_mentions
from dirty_product_linker.schemas import DataProvenance, MultiProductQuery


class EvaluationConfig(BaseModel):
    """Pinned inputs and role for a reproducible candidate-set run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    evaluation_id: str
    dataset_role: str
    expected_provenance: DataProvenance
    dataset_path: Path
    expected_dataset_sha256: str
    manifest_path: Path | None = None
    expected_manifest_sha256: str | None = None
    catalog_path: Path
    expected_catalog_sha256: str
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/eval/multi_product_candidates_v0_1.yaml"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    config = EvaluationConfig.model_validate(
        yaml.safe_load(args.config.read_text(encoding="utf-8"))
    )
    dataset_sha256 = _sha256(config.dataset_path)
    catalog_sha256 = _sha256(config.catalog_path)
    if dataset_sha256 != config.expected_dataset_sha256:
        raise ValueError("candidate dataset checksum mismatch")
    if catalog_sha256 != config.expected_catalog_sha256:
        raise ValueError("catalog checksum mismatch")
    manifest_sha256 = None
    manifest = None
    if config.manifest_path is not None:
        manifest_sha256 = _sha256(config.manifest_path)
        if manifest_sha256 != config.expected_manifest_sha256:
            raise ValueError("review manifest checksum mismatch")
        manifest = json.loads(config.manifest_path.read_text(encoding="utf-8"))
        if manifest.get("reviewed_sha256") != dataset_sha256:
            raise ValueError("review manifest does not match frozen dataset")

    examples = [
        MultiProductQuery.model_validate_json(line)
        for line in config.dataset_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    unexpected_provenance = [
        example.query_id
        for example in examples
        if example.provenance is not config.expected_provenance
    ]
    if unexpected_provenance:
        raise ValueError(
            "dataset provenance mismatch for query IDs: "
            f"{unexpected_provenance}"
        )
    if manifest is not None and manifest.get("example_count") != len(examples):
        raise ValueError("review manifest example count mismatch")
    service = LexicalLinkingService.from_catalog(config.catalog_path)
    predictions = {
        example.query_id: service.extract_and_link(example.text) for example in examples
    }
    overall = evaluate_mentions(examples, predictions)
    slice_names = sorted({example.slice_name for example in examples})
    by_slice = {
        slice_name: asdict(
            evaluate_mentions(
                [example for example in examples if example.slice_name == slice_name],
                predictions,
            )
        )
        for slice_name in slice_names
    }
    report = {
        "schema_version": "1.0",
        "evaluation_id": config.evaluation_id,
        "dataset_role": config.dataset_role,
        "dataset_sha256": dataset_sha256,
        "catalog_sha256": catalog_sha256,
        "manifest_sha256": manifest_sha256,
        "review": manifest,
        "extractor": "catalog-longest-surface-v0.1",
        "metrics": {"overall": asdict(overall), "by_slice": by_slice},
        "predictions": [
            {
                "query_id": example.query_id,
                "slice_name": example.slice_name,
                "text": example.text,
                "gold_mentions": [
                    mention.model_dump() for mention in example.mentions
                ],
                "predicted_mentions": [
                    mention.model_dump() for mention in predictions[example.query_id].mentions
                ],
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

    print(
        f"span_f1={overall.exact_span_f1:.3f}; "
        f"linking={overall.linking_accuracy_on_exact_spans:.3f}; "
        f"end_to_end={overall.end_to_end_mention_accuracy:.3f}; "
        f"query_exact={overall.query_exact_match:.3f}; "
        f"negative_accuracy={overall.negative_accuracy:.3f}"
    )


if __name__ == "__main__":
    main()
