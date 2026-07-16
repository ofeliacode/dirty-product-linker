"""Dense embedding retrieval with an optional SentenceTransformers adapter."""

import math
from collections.abc import Sequence
from importlib import import_module
from typing import Any, Protocol, cast

from dirty_product_linker.linking.lexical import LinkCandidate, LinkResult
from dirty_product_linker.schemas import Product


class EmbeddingEncoder(Protocol):
    """Minimal encoder interface required by dense product retrieval."""

    def encode(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Return one equal-length numeric vector per input text."""
        ...


class SentenceTransformerEncoder:
    """Pinned Hugging Face SentenceTransformer loaded only when requested."""

    def __init__(
        self,
        *,
        model_id: str,
        revision: str,
        device: str = "cpu",
    ) -> None:
        try:
            module = import_module("sentence_transformers")
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "embedding support is not installed; run pip install -e '.[embeddings]'"
            ) from error
        sentence_transformer: Any = module.SentenceTransformer
        self._model: Any = sentence_transformer(
            model_id,
            revision=revision,
            device=device,
        )

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode and L2-normalize a batch for cosine similarity."""

        vectors: Any = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return cast(list[list[float]], vectors.tolist())


def _product_document(product: Product) -> str:
    parts = [
        product.brand,
        product.family or "",
        product.model,
        product.category.value,
        *product.aliases,
        *(str(value) for _, value in sorted(product.attributes.items())),
    ]
    return "; ".join(part for part in parts if part)


def _validate_vectors(
    vectors: Sequence[Sequence[float]],
    *,
    expected_count: int,
) -> tuple[tuple[float, ...], ...]:
    if len(vectors) != expected_count:
        raise ValueError(
            f"encoder returned {len(vectors)} vectors for {expected_count} texts"
        )
    dimensions = {len(vector) for vector in vectors}
    if len(dimensions) != 1 or not dimensions or next(iter(dimensions)) < 1:
        raise ValueError("embedding dimensions must be equal and non-empty")
    return tuple(tuple(float(value) for value in vector) for vector in vectors)


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding dimensions must match")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )


class EmbeddingProductLinker:
    """Pre-encode a catalog and rank it by cosine similarity per query."""

    def __init__(
        self,
        products: list[Product],
        *,
        encoder: EmbeddingEncoder,
        min_score: float,
    ) -> None:
        if not products:
            raise ValueError("products cannot be empty")
        if not -1 <= min_score <= 1:
            raise ValueError("min_score must be between minus one and one")
        sorted_products = sorted(products, key=lambda item: item.product_id)
        documents = [_product_document(product) for product in sorted_products]
        vectors = _validate_vectors(
            encoder.encode(documents),
            expected_count=len(sorted_products),
        )
        self._encoder = encoder
        self._min_score = min_score
        self._index = tuple(
            (product.product_id, document, vector)
            for product, document, vector in zip(
                sorted_products, documents, vectors, strict=True
            )
        )

    def link(self, text: str, *, top_k: int = 5) -> LinkResult:
        """Encode a query, rank catalog documents, and abstain below threshold."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_vectors = _validate_vectors(self._encoder.encode([text]), expected_count=1)
        query_vector = query_vectors[0]
        candidates = tuple(
            sorted(
                (
                    LinkCandidate(
                        product_id=product_id,
                        score=round(_cosine(query_vector, vector), 6),
                        matched_surface=document,
                    )
                    for product_id, document, vector in self._index
                ),
                key=lambda item: (-item.score, item.product_id),
            )[:top_k]
        )
        best = candidates[0]
        if best.score < self._min_score:
            return LinkResult(
                status="unknown",
                product_id=None,
                score=best.score,
                candidates=candidates,
            )
        return LinkResult(
            status="linked",
            product_id=best.product_id,
            score=best.score,
            candidates=candidates,
        )
