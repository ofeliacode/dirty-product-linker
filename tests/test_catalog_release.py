import hashlib
import json
from pathlib import Path

from dirty_product_linker.catalog.release import build_release_from_config, write_catalog_release
from dirty_product_linker.schemas import Product, ProductCategory


def make_product(product_id: str, category: ProductCategory) -> Product:
    return Product(
        product_id=product_id,
        category=category,
        brand="Example",
        model=product_id,
        aliases=[product_id],
    )


def test_release_writes_valid_jsonl_and_matching_checksum(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog_v1.jsonl"
    manifest_path = tmp_path / "catalog_v1_manifest.json"
    products = [
        make_product("phone-1", ProductCategory.SMARTPHONE),
        make_product("phone-2", ProductCategory.SMARTPHONE),
        make_product("phone-3", ProductCategory.SMARTPHONE),
        make_product("laptop-1", ProductCategory.LAPTOP),
    ]

    result = write_catalog_release(
        products,
        catalog_path=catalog_path,
        manifest_path=manifest_path,
        catalog_version="catalog-v1",
        per_category_limit=2,
        seed=42,
    )

    catalog_bytes = catalog_path.read_bytes()
    rows = [
        Product.model_validate_json(line)
        for line in catalog_bytes.decode().splitlines()
        if line
    ]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(rows) == 3
    assert len(result.products) == 3
    assert manifest["catalog_version"] == "catalog-v1"
    assert manifest["input_count"] == 4
    assert manifest["category_counts"] == {"laptop": 1, "smartphone": 2}
    assert manifest["sha256"] == hashlib.sha256(catalog_bytes).hexdigest()


def test_same_inputs_create_byte_identical_releases(tmp_path: Path) -> None:
    products = [
        make_product(f"phone-{index}", ProductCategory.SMARTPHONE)
        for index in range(10)
    ]
    first_catalog = tmp_path / "first.jsonl"
    second_catalog = tmp_path / "second.jsonl"

    write_catalog_release(
        products,
        catalog_path=first_catalog,
        manifest_path=tmp_path / "first-manifest.json",
        catalog_version="catalog-v1",
        per_category_limit=3,
        seed=42,
    )
    write_catalog_release(
        reversed(products),
        catalog_path=second_catalog,
        manifest_path=tmp_path / "second-manifest.json",
        catalog_version="catalog-v1",
        per_category_limit=3,
        seed=42,
    )

    assert first_catalog.read_bytes() == second_catalog.read_bytes()


def test_build_release_from_yaml_config(tmp_path: Path) -> None:
    input_path = tmp_path / "imported.jsonl"
    output_path = tmp_path / "catalog_v1.jsonl"
    manifest_path = tmp_path / "manifest.json"
    config_path = tmp_path / "catalog_v1.yaml"
    products = [
        make_product("phone-1", ProductCategory.SMARTPHONE),
        make_product("phone-2", ProductCategory.SMARTPHONE),
    ]
    input_path.write_text(
        "".join(product.model_dump_json() + "\n" for product in products),
        encoding="utf-8",
    )
    config_path.write_text(
        "\n".join(
            [
                'schema_version: "1.0"',
                "catalog_version: catalog-v1",
                f"input_path: {input_path}",
                f"output_path: {output_path}",
                f"manifest_path: {manifest_path}",
                "per_category_limit: 1",
                "seed: 42",
            ]
        ),
        encoding="utf-8",
    )

    result = build_release_from_config(config_path)

    assert len(result.products) == 1
    assert output_path.exists()
    assert manifest_path.exists()
