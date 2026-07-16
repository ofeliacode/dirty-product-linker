import json
from pathlib import Path

import pytest

from dirty_product_linker.benchmark.freeze import freeze_benchmark
from dirty_product_linker.schemas import AnnotatedQuery, Product


def product(product_id: str) -> Product:
    return Product(
        product_id=product_id,
        category="smartphone",
        brand="Example",
        model=product_id,
    )


def query(
    query_id: str,
    *,
    provenance: str = "human",
    answerable: bool = True,
) -> AnnotatedQuery:
    return AnnotatedQuery.model_validate(
        {
            "query_id": query_id,
            "text": "ищу phone",
            "language": "ru-mixed",
            "noise_types": ["mixed_script"],
            "entities": [
                {
                    "type": "MODEL",
                    "start": 4,
                    "end": 9,
                    "text": "phone",
                    "normalized": "Phone",
                }
            ],
            "target_product_ids": ["phone-1"] if answerable else [],
            "answerable": answerable,
            "provenance": provenance,
        }
    )


def test_freeze_writes_deterministic_dataset_and_manifest(tmp_path: Path) -> None:
    output_path = tmp_path / "benchmark.jsonl"
    manifest_path = tmp_path / "manifest.json"
    slices = {
        "dirty": [query("dirty-1")],
        "negative": [query("negative-1", answerable=False)],
    }

    result = freeze_benchmark(
        slices=slices,
        catalog=[product("phone-1")],
        output_path=output_path,
        manifest_path=manifest_path,
        benchmark_version="ru-dirty-v0.1",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result.example_count == 2
    assert manifest["slice_counts"] == {"dirty": 1, "negative": 1}
    assert manifest["sha256"] == result.sha256
    assert manifest["catalog_product_ids_sha256"] == result.catalog_product_ids_sha256
    assert output_path.read_text(encoding="utf-8").splitlines()[0].startswith(
        '{"slice":"dirty"'
    )


def test_freeze_rejects_ai_generated_candidates(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="human-reviewed"):
        freeze_benchmark(
            slices={"dirty": [query("dirty-1", provenance="synthetic")]},
            catalog=[product("phone-1")],
            output_path=tmp_path / "benchmark.jsonl",
            manifest_path=tmp_path / "manifest.json",
            benchmark_version="ru-dirty-v0.1",
        )


def test_freeze_rejects_unknown_target_product(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown target product"):
        freeze_benchmark(
            slices={"dirty": [query("dirty-1")]},
            catalog=[product("different-phone")],
            output_path=tmp_path / "benchmark.jsonl",
            manifest_path=tmp_path / "manifest.json",
            benchmark_version="ru-dirty-v0.1",
        )


def test_freeze_rejects_duplicate_query_ids_across_slices(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate query_id"):
        freeze_benchmark(
            slices={"dirty": [query("same-1")], "negative": [query("same-1")]},
            catalog=[product("phone-1")],
            output_path=tmp_path / "benchmark.jsonl",
            manifest_path=tmp_path / "manifest.json",
            benchmark_version="ru-dirty-v0.1",
        )
