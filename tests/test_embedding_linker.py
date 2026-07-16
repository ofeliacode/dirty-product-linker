from collections.abc import Sequence

from dirty_product_linker.linking.embedding import EmbeddingProductLinker
from dirty_product_linker.schemas import Product


class FakeEncoder:
    """Tiny semantic space used to test ranking without an ML dependency."""

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            normalized = text.casefold()
            if "iphone" in normalized or "айфон" in normalized:
                vectors.append([1.0, 0.0])
            elif "samsung" in normalized or "самсунг" in normalized:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([-1.0, -1.0])
        return vectors


def products() -> list[Product]:
    return [
        Product(
            product_id="apple-iphone-15-pro-max-256-black",
            category="smartphone",
            brand="Apple",
            family="iPhone",
            model="iPhone 15 Pro Max",
            aliases=["айфон 15 про макс", "15pm"],
        ),
        Product(
            product_id="samsung-galaxy-s24-ultra-256-gray",
            category="smartphone",
            brand="Samsung",
            family="Galaxy S",
            model="Galaxy S24 Ultra",
            aliases=["самсунг с24 ультра", "s24u"],
        ),
    ]


def test_embedding_linker_ranks_semantically_matching_product() -> None:
    linker = EmbeddingProductLinker(products(), encoder=FakeEncoder(), min_score=0.5)

    result = linker.link("хочу айфон", top_k=2)

    assert result.status == "linked"
    assert result.product_id == "apple-iphone-15-pro-max-256-black"
    assert result.candidates[0].score == 1.0


def test_embedding_linker_abstains_below_similarity_threshold() -> None:
    linker = EmbeddingProductLinker(products(), encoder=FakeEncoder(), min_score=0.5)

    result = linker.link("неизвестный товар", top_k=2)

    assert result.status == "unknown"
    assert result.product_id is None


def test_embedding_linker_validates_encoder_dimensions() -> None:
    class BrokenEncoder:
        def encode(self, texts: Sequence[str]) -> list[list[float]]:
            return [[1.0]] if len(texts) == 1 else [[1.0], [1.0, 2.0]]

    try:
        EmbeddingProductLinker(products(), encoder=BrokenEncoder(), min_score=0.5)
    except ValueError as error:
        assert "embedding dimensions" in str(error)
    else:
        raise AssertionError("dimension mismatch must be rejected")
