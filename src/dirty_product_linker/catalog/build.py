"""Deterministic deduplication and balancing for a catalog release."""

import hashlib
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from dirty_product_linker.schemas import Product, ProductCategory


@dataclass(frozen=True, slots=True)
class DeduplicationResult:
    """Unique products and the number of repeated catalog records removed."""

    products: tuple[Product, ...]
    duplicates_removed: int


@dataclass(frozen=True, slots=True)
class CatalogBuildResult:
    """A balanced, reproducible catalog selection with build statistics."""

    products: tuple[Product, ...]
    input_count: int
    deduplicated_count: int
    duplicates_removed: int
    category_counts: dict[ProductCategory, int]
    per_category_limit: int
    seed: int


def canonical_catalog_text(value: str) -> str:
    """Normalize text for conservative exact-product deduplication."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    words = "".join(character if character.isalnum() else " " for character in normalized)
    return " ".join(words.split())


def deduplicate_products(products: Iterable[Product]) -> DeduplicationResult:
    """Keep the first record for each normalized category, brand, and model key."""

    unique: list[Product] = []
    seen: set[tuple[ProductCategory, str, str]] = set()
    duplicates_removed = 0

    for product in products:
        key = (
            product.category,
            canonical_catalog_text(product.brand),
            canonical_catalog_text(product.model),
        )
        if key in seen:
            duplicates_removed += 1
            continue
        seen.add(key)
        unique.append(product)

    return DeduplicationResult(tuple(unique), duplicates_removed)


def _seeded_rank(product: Product, seed: int) -> str:
    value = f"{seed}:{product.product_id}".encode()
    return hashlib.sha256(value).hexdigest()


def build_balanced_catalog(
    products: Iterable[Product],
    *,
    per_category_limit: int,
    seed: int,
) -> CatalogBuildResult:
    """Deduplicate and deterministically cap every represented category."""

    if per_category_limit < 1:
        raise ValueError("per_category_limit must be at least 1")

    materialized = tuple(products)
    deduplicated = deduplicate_products(materialized)
    grouped: defaultdict[ProductCategory, list[Product]] = defaultdict(list)
    for product in deduplicated.products:
        grouped[product.category].append(product)

    selected: list[Product] = []
    category_counts: dict[ProductCategory, int] = {}
    for category in sorted(grouped, key=lambda item: item.value):
        ranked = sorted(grouped[category], key=lambda product: _seeded_rank(product, seed))
        category_products = ranked[:per_category_limit]
        selected.extend(category_products)
        category_counts[category] = len(category_products)

    return CatalogBuildResult(
        products=tuple(selected),
        input_count=len(materialized),
        deduplicated_count=len(deduplicated.products),
        duplicates_removed=deduplicated.duplicates_removed,
        category_counts=category_counts,
        per_category_limit=per_category_limit,
        seed=seed,
    )
