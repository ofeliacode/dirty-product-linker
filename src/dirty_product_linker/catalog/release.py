"""Write a deterministic catalog release and its integrity manifest."""

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dirty_product_linker.catalog.build import CatalogBuildResult, build_balanced_catalog
from dirty_product_linker.catalog.shopify import SOURCE_ID, SOURCE_REVISION
from dirty_product_linker.schemas import Product


class CatalogReleaseConfig(BaseModel):
    """Validated paths and deterministic selection settings for one release."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    catalog_version: str
    input_path: Path
    output_path: Path
    manifest_path: Path
    per_category_limit: int = Field(ge=1)
    seed: int


def _replace_bytes(path: Path, content: bytes) -> None:
    """Write beside the destination and replace it only after completion."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def write_catalog_release(
    products: Iterable[Product],
    *,
    catalog_path: Path,
    manifest_path: Path,
    catalog_version: str,
    per_category_limit: int,
    seed: int,
) -> CatalogBuildResult:
    """Build, serialize, checksum, and describe one catalog release."""

    result = build_balanced_catalog(
        products,
        per_category_limit=per_category_limit,
        seed=seed,
    )
    catalog_content = (
        "".join(product.model_dump_json() + "\n" for product in result.products).encode()
    )
    _replace_bytes(catalog_path, catalog_content)

    manifest = {
        "schema_version": "1.0",
        "catalog_version": catalog_version,
        "source": SOURCE_ID,
        "source_revision": SOURCE_REVISION,
        "input_count": result.input_count,
        "deduplicated_count": result.deduplicated_count,
        "duplicates_removed": result.duplicates_removed,
        "output_count": len(result.products),
        "category_counts": {
            category.value: count
            for category, count in sorted(
                result.category_counts.items(),
                key=lambda item: item[0].value,
            )
        },
        "per_category_limit": result.per_category_limit,
        "seed": result.seed,
        "sha256": hashlib.sha256(catalog_content).hexdigest(),
    }
    manifest_content = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    _replace_bytes(manifest_path, manifest_content)
    return result


def build_release_from_config(config_path: Path) -> CatalogBuildResult:
    """Load imported products and build the release described by a YAML file."""

    with config_path.open(encoding="utf-8") as source:
        config = CatalogReleaseConfig.model_validate(yaml.safe_load(source))

    with config.input_path.open(encoding="utf-8") as source:
        products = [Product.model_validate_json(line) for line in source if line.strip()]

    return write_catalog_release(
        products,
        catalog_path=config.output_path,
        manifest_path=config.manifest_path,
        catalog_version=config.catalog_version,
        per_category_limit=config.per_category_limit,
        seed=config.seed,
    )
