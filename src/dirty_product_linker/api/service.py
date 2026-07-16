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
from dirty_product_linker.linking.lexical import LexicalProductLinker
from dirty_product_linker.schemas import Product

CATALOG_VERSION = "demo-catalog-v0.2"


class LinkingService(Protocol):
    """Small boundary that lets tests and future runtimes replace the baseline."""

    def analyze(self, text: str) -> AnalysisResponse:
        """Resolve one noisy product mention."""


class LexicalLinkingService:
    """Load a catalog once and reuse an in-memory linker across requests."""

    def __init__(self, products: Sequence[Product], *, catalog_version: str) -> None:
        self._products = {product.product_id: product for product in products}
        self._linker = LexicalProductLinker(list(products), min_score=0.42)
        self._catalog_version = catalog_version

    @classmethod
    def from_catalog(cls, path: Path) -> "LexicalLinkingService":
        """Build a service from the project's deterministic JSONL catalog."""

        with path.open(encoding="utf-8") as source:
            products = [
                Product.model_validate_json(line) for line in source if line.strip()
            ]
        return cls(products, catalog_version=CATALOG_VERSION)

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
            decision_source="lexical",
            score=result.score,
            processing_ms=round((perf_counter() - started_at) * 1000, 3),
            catalog_version=self._catalog_version,
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
