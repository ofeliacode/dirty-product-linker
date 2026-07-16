import pytest
from pydantic import ValidationError

from dirty_product_linker.schemas import (
    AnnotatedQuery,
    EntityAnnotation,
    EntityType,
    Product,
)


def test_product_accepts_a_canonical_catalog_record() -> None:
    product = Product.model_validate(
        {
            "product_id": "apple-iphone-15-pro-max-256-black",
            "category": "smartphone",
            "brand": "Apple",
            "family": "iPhone",
            "model": "iPhone 15 Pro Max",
            "attributes": {"storage_gb": 256, "color": "black"},
            "aliases": ["айфон 15 про макс", "15pm"],
        }
    )

    assert product.product_id == "apple-iphone-15-pro-max-256-black"
    assert product.attributes["storage_gb"] == 256


def test_product_rejects_an_empty_alias() -> None:
    with pytest.raises(ValidationError):
        Product.model_validate(
            {
                "product_id": "sony-wh-1000xm5-black",
                "category": "headphones",
                "brand": "Sony",
                "model": "WH-1000XM5",
                "aliases": [""],
            }
        )


def test_annotated_query_accepts_offsets_that_match_entity_text() -> None:
    query = AnnotatedQuery.model_validate(
        {
            "query_id": "query-0001",
            "text": "хочу 15pm на 256",
            "language": "ru-mixed",
            "noise_types": ["abbreviation", "missing_brand"],
            "entities": [
                {
                    "type": "MODEL",
                    "start": 5,
                    "end": 9,
                    "text": "15pm",
                    "normalized": "iPhone 15 Pro Max",
                }
            ],
            "target_product_ids": ["apple-iphone-15-pro-max-256-black"],
            "answerable": True,
            "provenance": "human",
        }
    )

    assert query.entities[0].type is EntityType.MODEL


def test_annotated_query_rejects_offsets_that_do_not_match_entity_text() -> None:
    with pytest.raises(ValidationError, match="entity offsets do not match"):
        AnnotatedQuery.model_validate(
            {
                "query_id": "query-0002",
                "text": "хочу 15pm",
                "language": "ru-mixed",
                "entities": [
                    {
                        "type": "MODEL",
                        "start": 0,
                        "end": 4,
                        "text": "15pm",
                        "normalized": "iPhone 15 Pro Max",
                    }
                ],
                "target_product_ids": ["apple-iphone-15-pro-max-256-black"],
                "answerable": True,
                "provenance": "human",
            }
        )


def test_entity_rejects_an_inverted_span() -> None:
    with pytest.raises(ValidationError):
        EntityAnnotation(
            type=EntityType.BRAND,
            start=8,
            end=3,
            text="Apple",
            normalized="Apple",
        )


def test_unanswerable_query_cannot_have_target_products() -> None:
    with pytest.raises(ValidationError, match="unanswerable query cannot have target products"):
        AnnotatedQuery.model_validate(
            {
                "query_id": "query-0003",
                "text": "когда привезут заказ",
                "language": "ru",
                "entities": [],
                "target_product_ids": ["apple-iphone-15-pro-max-256-black"],
                "answerable": False,
                "provenance": "human",
            }
        )
