import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dirty_product_linker.catalog.pipeline import stream_shopify_rows, write_shopify_import
from dirty_product_linker.catalog.taxonomy import TaxonomyMap
from dirty_product_linker.schemas import Product

PROJECT_ROOT = Path(__file__).parents[1]
TAXONOMY = TaxonomyMap.from_yaml(PROJECT_ROOT / "configs/data/taxonomy.yaml")


def load_fixture_rows() -> list[dict[str, object]]:
    path = PROJECT_ROOT / "tests/fixtures/shopify_products.jsonl"
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def test_pipeline_writes_valid_products_and_audit_report(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.jsonl"
    report_path = tmp_path / "report.json"

    result = write_shopify_import(
        load_fixture_rows(),
        catalog_path=catalog_path,
        report_path=report_path,
        taxonomy=TAXONOMY,
    )

    with catalog_path.open(encoding="utf-8") as source:
        products = [Product.model_validate_json(line) for line in source if line.strip()]
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert len(products) == 5
    assert result.accepted == 5
    assert report == {
        "accepted": 5,
        "dataset_id": "Shopify/product-catalogue",
        "read": 7,
        "rejected": 2,
        "rejection_reasons": {
            "missing_brand": 1,
            "unsupported_category": 1,
        },
        "revision": "d5c517c509f5aca99053897ef1de797d6d7e5aa5",
        "schema_version": "1.0",
    }


def test_stream_selects_text_columns_before_image_decoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_row: dict[str, object] = {
        "product_title": "Phone",
        "product_description": "Description",
        "product_image": {"bytes": b"not-an-image"},
        "ground_truth_brand": "Brand",
        "ground_truth_category": "Electronics > Mobile Phones",
        "ground_truth_is_secondhand": False,
    }

    class FakeDataset:
        selected_columns: list[str] | None = None
        skipped = 0

        def select_columns(self, columns: list[str]) -> "FakeDataset":
            self.selected_columns = columns
            return self

        def skip(self, count: int) -> "FakeDataset":
            self.skipped = count
            return self

        def __iter__(self):  # type: ignore[no-untyped-def]
            rows = [
                {column: source_row[column] for column in self.selected_columns or []}
                for _ in range(5)
            ]
            return iter(rows[self.skipped :])

    fake_dataset = FakeDataset()
    load_arguments: dict[str, object] = {}

    def fake_load_dataset(dataset_id: str, **kwargs: object) -> FakeDataset:
        load_arguments.update({"dataset_id": dataset_id, **kwargs})
        return fake_dataset

    monkeypatch.setattr(
        "dirty_product_linker.catalog.pipeline.import_module",
        lambda _: SimpleNamespace(load_dataset=fake_load_dataset),
    )

    rows = list(stream_shopify_rows(limit=3, skip=2))

    assert "product_image" not in rows[0]
    assert len(rows) == 1
    assert fake_dataset.skipped == 2
    assert fake_dataset.selected_columns == [
        "product_title",
        "product_description",
        "ground_truth_brand",
        "ground_truth_category",
        "ground_truth_is_secondhand",
    ]
    assert load_arguments["streaming"] is True
