"""Production-shaped runtime service backed by the lightweight baseline."""

from collections.abc import Sequence
from pathlib import Path
from time import perf_counter
from typing import Protocol

from dirty_product_linker.api.schemas import (
    AnalysisResponse,
    CandidateResponse,
    ProductSummary,
)
from dirty_product_linker.linking.embedding import EmbeddingEncoder, EmbeddingProductLinker
from dirty_product_linker.linking.lexical import LexicalProductLinker, LinkResult
from dirty_product_linker.linking.pipeline import EndToEndProductLinker
from dirty_product_linker.linking.reranker import FeatureAwareReranker
from dirty_product_linker.schemas import Product

CATALOG_VERSION = "demo-catalog-v0.2"
LEXICAL_MODEL_VERSION = "lexical-v0.2"
RERANKER_MODEL_VERSION = "feature-reranker-v0.1.0"


class LinkingService(Protocol):
    """Small boundary that lets tests and future runtimes replace the baseline."""

    def analyze(self, text: str) -> AnalysisResponse:
        """Resolve one noisy product mention."""


class ResultLinker(Protocol):
    """Linker boundary shared by lightweight and end-to-end runtimes."""

    def link(self, text: str, *, top_k: int = 5) -> LinkResult:
        """Return a final decision and ranked candidates."""


class ProductLinkingService:
    """Enrich a linking decision with catalog records and runtime metadata."""

    def __init__(
        self,
        products: Sequence[Product],
        *,
        linker: ResultLinker,
        model_version: str,
        catalog_version: str,
    ) -> None:
        self._products = {product.product_id: product for product in products}
        self._linker = linker
        self._model_version = model_version
        self._catalog_version = catalog_version

    def analyze(self, text: str) -> AnalysisResponse:
        """Run deterministic retrieval and enrich IDs with catalog metadata."""

        started_at = perf_counter()
        result = self._linker.link(text, top_k=5)
        candidates = [
            self._candidate(candidate.product_id, candidate.score, candidate.matched_surface)
            for candidate in result.candidates
        ]
        selected = (
            self._summary(self._products[result.product_id])
            if result.product_id is not None
            else None
        )
        return AnalysisResponse(
            text=text,
            status=result.status,
            # EndToEndProductLinker returns FeatureAwareResult with this field.
            # getattr keeps the same response mapper reusable for the lexical baseline.
            decision_source=getattr(result, "decision_source", "lexical"),
            score=result.score,
            confidence=result.score,
            processing_ms=round((perf_counter() - started_at) * 1000, 3),
            model_version=self._model_version,
            catalog_version=self._catalog_version,
            product_id=result.product_id,
            category=selected.category if selected is not None else None,
            selected_product=selected,
            candidates=candidates,
        )

    def _candidate(
        self, product_id: str, score: float, matched_surface: str
    ) -> CandidateResponse:
        product = self._products[product_id]
        return CandidateResponse(
            **self._summary(product).model_dump(),
            score=score,
            matched_surface=matched_surface,
        )

    @staticmethod
    def _summary(product: Product) -> ProductSummary:
        return ProductSummary(
            product_id=product.product_id,
            brand=product.brand,
            model=product.model,
            category=product.category.value,
        )


class LexicalLinkingService(ProductLinkingService):
    """Load a catalog once and reuse the lightweight lexical baseline."""

    @classmethod
    def from_catalog(cls, path: Path) -> "LexicalLinkingService":
        products = _load_products(path)
        return cls(
            products,
            linker=LexicalProductLinker(products, min_score=0.42),
            model_version=LEXICAL_MODEL_VERSION,
            catalog_version=CATALOG_VERSION,
        )


class EndToEndLinkingService(ProductLinkingService):
    """Production service combining lexical, dense, reranking, and abstention."""

    @classmethod
    def from_catalog(
        cls,
        path: Path,
        *,
        encoder: EmbeddingEncoder,
    ) -> "EndToEndLinkingService":
        products = _load_products(path)
        pipeline = EndToEndProductLinker(
            lexical=LexicalProductLinker(products, min_score=0.0),
            dense=EmbeddingProductLinker(products, encoder=encoder, min_score=-1.0),
            reranker=FeatureAwareReranker(
                products,
                min_score=0.40,
                min_margin=0.08,
            ),
            candidate_top_k=5,
        )
        return cls(
            products,
            linker=pipeline,
            model_version=RERANKER_MODEL_VERSION,
            catalog_version=CATALOG_VERSION,
        )


def _load_products(path: Path) -> list[Product]:
    with path.open(encoding="utf-8") as source:
        return [Product.model_validate_json(line) for line in source if line.strip()]
