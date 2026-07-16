import json
from pathlib import Path

import yaml

from dirty_product_linker.catalog.shopify import convert_shopify_record, import_shopify_records
from dirty_product_linker.schemas import ProductCategory

PROJECT_ROOT = Path(__file__).parents[1]


def load_fixture_rows() -> list[dict[str, object]]:
    path = PROJECT_ROOT / "tests/fixtures/shopify_products.jsonl"
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def test_source_registry_pins_license_revision_and_allowed_usage() -> None:
    path = PROJECT_ROOT / "configs/data/sources.yaml"
    with path.open(encoding="utf-8") as source:
        registry = yaml.safe_load(source)

    shopify = registry["sources"]["shopify_product_catalogue"]
    assert shopify["license"] == "apache-2.0"
    assert shopify["revision"] == "d5c517c509f5aca99053897ef1de797d6d7e5aa5"
    assert "entity_linking_ground_truth" in shopify["prohibited_purposes"]


def test_shopify_record_becomes_a_versioned_product() -> None:
    row = load_fixture_rows()[0]

    product = convert_shopify_record(row)

    assert product.category is ProductCategory.SMARTPHONE
    assert product.brand == "Apple"
    assert product.model == "Apple iPhone 15 Pro Max 256GB"
    assert product.aliases == ["Apple iPhone 15 Pro Max 256GB"]
    assert product.attributes["source"] == "Shopify/product-catalogue"


def test_product_ids_are_deterministic_for_the_same_source_record() -> None:
    row = load_fixture_rows()[0]

    first = convert_shopify_record(row)
    second = convert_shopify_record(row)

    assert first.product_id == second.product_id


def test_import_reports_supported_categories_and_rejection_reasons() -> None:
    result = import_shopify_records(load_fixture_rows())

    assert result.read == 7
    assert result.accepted == 5
    assert result.rejected == 2
    assert {product.category for product in result.products} == set(ProductCategory)
    assert result.rejection_reasons == {
        "missing_brand": 1,
        "unsupported_category": 1,
    }
