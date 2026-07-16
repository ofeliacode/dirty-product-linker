import hashlib
import json
from collections import Counter
from pathlib import Path

from dirty_product_linker.schemas import Product, ProductCategory

PROJECT_ROOT = Path(__file__).parents[1]


def load_products(path: Path) -> list[Product]:
    with path.open(encoding="utf-8") as source:
        return [Product.model_validate(json.loads(line)) for line in source if line.strip()]


def test_demo_catalog_v0_2_has_balanced_close_candidate_matrix() -> None:
    products = load_products(PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl")

    assert len(products) == 20
    assert len({product.product_id for product in products}) == 20
    assert Counter(product.category for product in products) == {
        category: 4 for category in ProductCategory
    }


def test_demo_catalog_v0_2_preserves_every_frozen_v0_1_product() -> None:
    old_products = {
        product.product_id: product
        for product in load_products(PROJECT_ROOT / "data/catalog/sample_catalog.jsonl")
    }
    new_products = {
        product.product_id: product
        for product in load_products(
            PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"
        )
    }

    assert old_products.keys() <= new_products.keys()
    for product_id, old_product in old_products.items():
        assert new_products[product_id] == old_product


def test_demo_catalog_v0_2_checksum_is_versioned() -> None:
    path = PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"

    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "9ba193ce8098b411febd3ff9d55a2c30210580aa8adf8e7d92b6ae0e345c6526"
    )
