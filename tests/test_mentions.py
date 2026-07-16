from dirty_product_linker.linking.mentions import CatalogMentionExtractor
from dirty_product_linker.schemas import Product, ProductCategory


def product(product_id: str, model: str, aliases: list[str]) -> Product:
    return Product(
        product_id=product_id,
        category=ProductCategory.SMARTPHONE,
        brand="Example",
        model=model,
        aliases=aliases,
    )


def test_extracts_multiple_longest_mentions_with_exact_source_offsets() -> None:
    text = "нужен айфон 15 про макс и наушники sony xm5 сегодня"
    extractor = CatalogMentionExtractor(
        [
            product("iphone", "iPhone 15 Pro Max", ["айфон 15 про макс"]),
            product("sony", "WH-1000XM5", ["sony xm5", "наушники sony xm5"]),
        ]
    )

    mentions = extractor.extract(text)

    assert [(item.text, item.start, item.end) for item in mentions] == [
        ("айфон 15 про макс", 6, 23),
        ("наушники sony xm5", 26, 43),
    ]
    assert all(text[item.start : item.end] == item.text for item in mentions)


def test_does_not_extract_generic_category_language() -> None:
    extractor = CatalogMentionExtractor(
        [product("iphone", "iPhone 15 Pro Max", ["айфон 15 про макс"])]
    )

    assert extractor.extract("посоветуй какой-нибудь хороший телефон") == ()
