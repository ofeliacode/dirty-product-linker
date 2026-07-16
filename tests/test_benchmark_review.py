import json
from pathlib import Path

import pytest

from dirty_product_linker.benchmark.review import (
    promote_reviewed_candidates,
    promote_reviewed_multi_product_candidates,
)
from dirty_product_linker.schemas import AnnotatedQuery, MultiProductQuery


def candidate(query_id: str, provenance: str = "synthetic") -> AnnotatedQuery:
    return AnnotatedQuery.model_validate(
        {
            "query_id": query_id,
            "text": "ищу phone",
            "language": "ru-mixed",
            "noise_types": ["mixed_script"],
            "entities": [],
            "target_product_ids": ["phone-1"],
            "answerable": True,
            "provenance": provenance,
        }
    )


def test_promotion_writes_human_reviewed_rows_and_attestation(tmp_path: Path) -> None:
    reviewed_dir = tmp_path / "reviewed"
    manifest_path = tmp_path / "review_manifest.json"

    result = promote_reviewed_candidates(
        slices={"dirty": [candidate("dirty-1")]},
        reviewed_dir=reviewed_dir,
        manifest_path=manifest_path,
        reviewer="ofeliacode",
        reviewed_at="2026-07-16",
    )

    row = AnnotatedQuery.model_validate_json(
        (reviewed_dir / "dirty.jsonl").read_text(encoding="utf-8").strip()
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert row.provenance == "human"
    assert result.example_count == 1
    assert manifest["reviewer"] == "ofeliacode"
    assert manifest["candidate_sha256"] == result.candidate_sha256


def test_promotion_refuses_rows_already_claimed_as_human(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="expected synthetic candidate"):
        promote_reviewed_candidates(
            slices={"dirty": [candidate("dirty-1", provenance="human")]},
            reviewed_dir=tmp_path / "reviewed",
            manifest_path=tmp_path / "manifest.json",
            reviewer="ofeliacode",
            reviewed_at="2026-07-16",
        )


def multi_candidate(provenance: str = "synthetic") -> MultiProductQuery:
    return MultiProductQuery.model_validate(
        {
            "query_id": "multi-1",
            "text": "нужен alpha",
            "language": "ru-mixed",
            "slice_name": "explicit_alias",
            "mentions": [
                {
                    "start": 6,
                    "end": 11,
                    "text": "alpha",
                    "product_id": "product-a",
                }
            ],
            "provenance": provenance,
        }
    )


def test_multi_product_promotion_writes_reviewed_file_and_manifest(
    tmp_path: Path,
) -> None:
    reviewed_path = tmp_path / "multi_product.jsonl"
    manifest_path = tmp_path / "manifest.json"

    result = promote_reviewed_multi_product_candidates(
        queries=[multi_candidate()],
        reviewed_path=reviewed_path,
        manifest_path=manifest_path,
        reviewer="ofeliacode",
        reviewed_at="2026-07-16",
    )

    row = MultiProductQuery.model_validate_json(
        reviewed_path.read_text(encoding="utf-8").strip()
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert row.provenance == "human"
    assert result.example_count == 1
    assert manifest["benchmark_type"] == "multi_product_extraction"
    assert manifest["reviewed_sha256"] == result.reviewed_sha256


def test_multi_product_promotion_refuses_false_human_provenance(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="expected synthetic candidate"):
        promote_reviewed_multi_product_candidates(
            queries=[multi_candidate("human")],
            reviewed_path=tmp_path / "reviewed.jsonl",
            manifest_path=tmp_path / "manifest.json",
            reviewer="ofeliacode",
            reviewed_at="2026-07-16",
        )
