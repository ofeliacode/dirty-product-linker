from dirty_product_linker.linking.lexical import LexicalProductLinker
from dirty_product_linker.schemas import Product


def products() -> list[Product]:
    return [
        Product(
            product_id="apple-iphone-15-pro-max-256-black",
            category="smartphone",
            brand="Apple",
            family="iPhone",
            model="iPhone 15 Pro Max",
            attributes={"storage_gb": 256, "color": "black"},
            aliases=["айфон 15 про макс", "15pm"],
        ),
        Product(
            product_id="samsung-galaxy-s24-ultra-256-gray",
            category="smartphone",
            brand="Samsung",
            family="Galaxy S",
            model="Galaxy S24 Ultra",
            attributes={"storage_gb": 256, "color": "gray"},
            aliases=["самсунь s24 ultra", "s24u"],
        ),
    ]


def test_alias_abbreviation_links_to_the_expected_product() -> None:
    linker = LexicalProductLinker(products(), min_score=0.42)

    result = linker.link("ищу 15pm 256gb")

    assert result.status == "linked"
    assert result.product_id == "apple-iphone-15-pro-max-256-black"
    assert result.candidates[0].score >= 0.42


def test_unknown_out_of_catalog_model_abstains() -> None:
    linker = LexicalProductLinker(products(), min_score=0.42)

    result = linker.link("нужен pixel 9 pro")

    assert result.status == "unknown"
    assert result.product_id is None


def test_top_k_is_deterministic_when_scores_are_equal() -> None:
    same_a = Product(
        product_id="brand-model-a",
        category="smartphone",
        brand="Brand",
        model="Model",
        aliases=["same alias"],
    )
    same_b = same_a.model_copy(update={"product_id": "brand-model-b"})
    linker = LexicalProductLinker([same_b, same_a], min_score=0.42)

    result = linker.link("same alias", top_k=2)

    assert [candidate.product_id for candidate in result.candidates] == [
        "brand-model-a",
        "brand-model-b",
    ]
