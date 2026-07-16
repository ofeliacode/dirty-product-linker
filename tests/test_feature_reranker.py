from dirty_product_linker.linking.lexical import LinkCandidate, LinkResult
from dirty_product_linker.linking.reranker import FeatureAwareReranker
from dirty_product_linker.schemas import Product, ProductCategory


def raw_result(candidates: list[tuple[str, float]]) -> LinkResult:
    return LinkResult(
        status="linked",
        product_id=candidates[0][0],
        score=candidates[0][1],
        candidates=tuple(
            LinkCandidate(product_id, score, product_id)
            for product_id, score in candidates
        ),
    )


def test_category_and_attributes_resolve_same_brand_phone_vs_washer() -> None:
    phone = Product(
        product_id="samsung-phone",
        category=ProductCategory.SMARTPHONE,
        brand="Samsung",
        family="Galaxy S",
        model="Galaxy S24 Ultra",
        attributes={"storage_gb": 256, "color": "gray"},
    )
    washer = Product(
        product_id="samsung-washer",
        category=ProductCategory.HOME_APPLIANCE,
        brand="Samsung",
        family="WW5000T",
        model="WW90T554DAW",
        attributes={"color": "white", "capacity_kg": 9},
    )
    reranker = FeatureAwareReranker([phone, washer], min_score=0.4, min_margin=0.08)

    result = reranker.rerank(
        "белая стиральная машина samsung на 9 килограмм",
        lexical=raw_result([("samsung-phone", 0.25), ("samsung-washer", 0.2)]),
        dense=raw_result([("samsung-phone", 0.65), ("samsung-washer", 0.6)]),
    )

    assert result.status == "linked"
    assert result.product_id == "samsung-washer"
    assert result.features_by_product["samsung-washer"].brand_evidence == 1.0
    assert result.features_by_product["samsung-washer"].category_compatibility == 1.0


def test_generic_category_and_shared_size_abstain_without_identity_evidence() -> None:
    lg = Product(
        product_id="lg-tv",
        category=ProductCategory.TELEVISION,
        brand="LG",
        model="OLED C3",
        attributes={"screen_inches": 55},
    )
    sony = Product(
        product_id="sony-tv",
        category=ProductCategory.TELEVISION,
        brand="Sony",
        model="BRAVIA 8",
        attributes={"screen_inches": 55},
    )
    reranker = FeatureAwareReranker([lg, sony], min_score=0.4, min_margin=0.08)

    result = reranker.rerank(
        "хочу телевизор 55 дюймов",
        lexical=raw_result([("lg-tv", 0.2), ("sony-tv", 0.2)]),
        dense=raw_result([("sony-tv", 0.7), ("lg-tv", 0.68)]),
    )

    assert result.status == "unknown"
    assert result.product_id is None
    assert result.decision_source == "abstain_no_identity"


def test_phonetic_brand_evidence_selects_pixel_from_union_candidates() -> None:
    pixel = Product(
        product_id="google-pixel",
        category=ProductCategory.SMARTPHONE,
        brand="Google",
        family="Pixel",
        model="Pixel 8 Pro",
    )
    oneplus = Product(
        product_id="oneplus-12",
        category=ProductCategory.SMARTPHONE,
        brand="OnePlus",
        model="OnePlus 12",
    )
    reranker = FeatureAwareReranker([pixel, oneplus], min_score=0.4, min_margin=0.08)

    result = reranker.rerank(
        "телефон гугл с хорошей камерой",
        lexical=raw_result([("oneplus-12", 0.2), ("google-pixel", 0.1)]),
        dense=raw_result([("oneplus-12", 0.55), ("google-pixel", 0.5)]),
    )

    assert result.status == "linked"
    assert result.product_id == "google-pixel"
    assert result.decision_source == "feature_reranker"
