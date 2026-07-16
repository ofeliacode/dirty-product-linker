"""Production-shaped runtime service backed by the lightweight baseline."""

from collections.abc import Callable, Sequence
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Protocol

from dirty_product_linker.api.schemas import (
    AnalysisResponse,
    CandidateResponse,
    DecisionReason,
    ProductSummary,
)
from dirty_product_linker.linking.embedding import (
    EmbeddingEncoder,
    EmbeddingProductLinker,
    SentenceTransformerEncoder,
)
from dirty_product_linker.linking.lexical import LexicalProductLinker, LinkResult
from dirty_product_linker.linking.pipeline import EndToEndProductLinker
from dirty_product_linker.linking.reranker import FeatureAwareReranker, detect_brand
from dirty_product_linker.schemas import Product

CATALOG_VERSION = "demo-catalog-v0.2"
LEXICAL_MODEL_VERSION = "lexical-v0.2"
RERANKER_MODEL_VERSION = "feature-reranker-v0.1.1"
EMBEDDING_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_MODEL_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"


class LinkingService(Protocol):
    """Small boundary that lets tests and future runtimes replace the baseline."""

    def analyze(self, text: str) -> AnalysisResponse:
        """Resolve one noisy product mention."""


class LazyLinkingService:
    """Defer model allocation until the first inference request."""

    def __init__(self, factory: Callable[[], LinkingService]) -> None:
        self._factory = factory
        self._service: LinkingService | None = None
        self._lock = Lock()

    def analyze(self, text: str) -> AnalysisResponse:
        service = self._service
        if service is None:
            with self._lock:
                service = self._service
                if service is None:
                    service = self._factory()
                    self._service = service
        return service.analyze(text)


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
        detected_brand_key = detect_brand(text)
        detected_brand = self._display_brand(detected_brand_key)
        decision_source = getattr(result, "decision_source", "lexical")
        reason = self._decision_reason(
            status=result.status,
            decision_source=decision_source,
            detected_brand_key=detected_brand_key,
        )
        return AnalysisResponse(
            text=text,
            status=result.status,
            # EndToEndProductLinker returns FeatureAwareResult with this field.
            # getattr keeps the same response mapper reusable for the lexical baseline.
            decision_source=decision_source,
            score=result.score,
            confidence=result.score,
            processing_ms=round((perf_counter() - started_at) * 1000, 3),
            model_version=self._model_version,
            catalog_version=self._catalog_version,
            product_id=result.product_id,
            category=selected.category if selected is not None else None,
            reason=reason,
            detected_brand=detected_brand,
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

    def _display_brand(self, normalized_brand: str | None) -> str | None:
        if normalized_brand is None:
            return None
        return next(
            (
                product.brand
                for product in self._products.values()
                if product.brand.casefold() == normalized_brand
            ),
            normalized_brand.title(),
        )

    def _decision_reason(
        self,
        *,
        status: str,
        decision_source: str,
        detected_brand_key: str | None,
    ) -> DecisionReason | None:
        if status == "linked":
            return None
        catalog_brands = {product.brand.casefold() for product in self._products.values()}
        if detected_brand_key is not None and detected_brand_key not in catalog_brands:
            return "brand_not_in_catalog"
        reasons_by_source: dict[str, DecisionReason] = {
            "abstain_low_margin": "ambiguous_candidates",
            "abstain_no_identity": "missing_product_identity",
        }
        return reasons_by_source.get(decision_source, "low_score")

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

    @classmethod
    def from_sentence_transformer(
        cls,
        path: Path,
        *,
        device: str = "cpu",
        local_files_only: bool = False,
    ) -> "EndToEndLinkingService":
        """Load the pinned multilingual embedding model and complete runtime."""

        encoder = SentenceTransformerEncoder(
            model_id=EMBEDDING_MODEL_ID,
            revision=EMBEDDING_MODEL_REVISION,
            device=device,
            local_files_only=local_files_only,
        )
        return cls.from_catalog(path, encoder=encoder)


def build_runtime_service(
    mode: str,
    *,
    catalog_path: Path,
    device: str = "cpu",
    local_files_only: bool = False,
) -> LinkingService:
    """Build one explicitly selected runtime without silent model fallback."""

    if mode == "lexical":
        return LexicalLinkingService.from_catalog(catalog_path)
    if mode == "full":
        return EndToEndLinkingService.from_sentence_transformer(
            catalog_path,
            device=device,
            local_files_only=local_files_only,
        )
    raise ValueError(f"unsupported runtime mode: {mode!r}")


def _load_products(path: Path) -> list[Product]:
    with path.open(encoding="utf-8") as source:
        return [Product.model_validate_json(line) for line in source if line.strip()]
