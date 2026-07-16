from dirty_product_linker.catalog.build import build_balanced_catalog, deduplicate_products
from dirty_product_linker.schemas import Product, ProductCategory


def make_product(
    product_id: str,
    category: ProductCategory,
    brand: str,
    model: str,
) -> Product:
    return Product(
        product_id=product_id,
        category=category,
        brand=brand,
        model=model,
        aliases=[model],
    )


def test_deduplication_ignores_case_spacing_and_punctuation() -> None:
    products = [
        make_product(
            "apple-iphone-15-pro-first",
            ProductCategory.SMARTPHONE,
            "Apple",
            "iPhone 15 Pro",
        ),
        make_product(
            "apple-iphone-15-pro-second",
            ProductCategory.SMARTPHONE,
            "APPLE",
            "iPhone   15-Pro",
        ),
    ]

    result = deduplicate_products(products)

    assert [product.product_id for product in result.products] == [
        "apple-iphone-15-pro-first"
    ]
    assert result.duplicates_removed == 1


def test_deduplication_preserves_different_sku_attributes() -> None:
    products = [
        make_product(
            "apple-iphone-15-pro-256",
            ProductCategory.SMARTPHONE,
            "Apple",
            "iPhone 15 Pro 256GB",
        ),
        make_product(
            "apple-iphone-15-pro-512",
            ProductCategory.SMARTPHONE,
            "Apple",
            "iPhone 15 Pro 512GB",
        ),
    ]

    result = deduplicate_products(products)

    assert len(result.products) == 2
    assert result.duplicates_removed == 0


def test_balanced_catalog_caps_each_category_and_is_reproducible() -> None:
    products = [
        make_product(
            f"phone-{index}",
            ProductCategory.SMARTPHONE,
            "PhoneCo",
            f"Phone {index}",
        )
        for index in range(5)
    ] + [
        make_product(
            f"laptop-{index}",
            ProductCategory.LAPTOP,
            "LaptopCo",
            f"Laptop {index}",
        )
        for index in range(3)
    ]

    first = build_balanced_catalog(products, per_category_limit=2, seed=42)
    second = build_balanced_catalog(reversed(products), per_category_limit=2, seed=42)

    assert first.products == second.products
    assert first.category_counts == {
        ProductCategory.SMARTPHONE: 2,
        ProductCategory.LAPTOP: 2,
    }
    assert first.input_count == 8
    assert first.deduplicated_count == 8


def test_different_seeds_can_select_different_products() -> None:
    products = [
        make_product(
            f"headphones-{index}",
            ProductCategory.HEADPHONES,
            "AudioCo",
            f"Headphones {index}",
        )
        for index in range(20)
    ]

    first = build_balanced_catalog(products, per_category_limit=3, seed=1)
    second = build_balanced_catalog(products, per_category_limit=3, seed=2)

    assert {product.product_id for product in first.products} != {
        product.product_id for product in second.products
    }
