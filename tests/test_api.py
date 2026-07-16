from collections.abc import Sequence

from fastapi.testclient import TestClient

from dirty_product_linker.api.app import DEFAULT_CATALOG, create_app
from dirty_product_linker.api.schemas import (
    AnalysisResponse,
    CandidateResponse,
    ProductSummary,
)
from dirty_product_linker.api.service import (
    EndToEndLinkingService,
    LexicalLinkingService,
)


class StubService:
    def analyze(self, text: str) -> AnalysisResponse:
        return AnalysisResponse(
            text=text,
            status="linked",
            decision_source="lexical",
            score=0.88,
            confidence=0.88,
            processing_ms=0.12,
            model_version="lexical-v0.2",
            catalog_version="demo-catalog-v0.2",
            product_id="apple-iphone-15-pro-max-256-black",
            category="smartphone",
            selected_product=ProductSummary(
                product_id="apple-iphone-15-pro-max-256-black",
                brand="Apple",
                model="iPhone 15 Pro Max",
                category="smartphone",
            ),
            candidates=[
                CandidateResponse(
                    product_id="apple-iphone-15-pro-max-256-black",
                    brand="Apple",
                    model="iPhone 15 Pro Max",
                    category="smartphone",
                    score=0.88,
                    matched_surface="15pm",
                )
            ],
        )


def client() -> TestClient:
    return TestClient(create_app(service=StubService()))


def test_health_reports_ready_without_exposing_internal_details() -> None:
    response = client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "dirty-product-linker"}


def test_link_endpoint_returns_versioned_explainable_contract() -> None:
    response = client().post("/v1/link", json={"text": "ищу 15pm на 256"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "linked"
    assert body["decision_source"] == "lexical"
    assert body["selected_product"]["model"] == "iPhone 15 Pro Max"
    assert body["candidates"][0]["score"] == 0.88
    assert body["confidence"] == 0.88
    assert body["product_id"] == "apple-iphone-15-pro-max-256-black"
    assert body["model_version"] == "lexical-v0.2"
    assert body["catalog_version"] == "demo-catalog-v0.2"


def test_link_endpoint_rejects_blank_or_oversized_text() -> None:
    blank = client().post("/v1/link", json={"text": "   "})
    oversized = client().post("/v1/link", json={"text": "x" * 501})

    assert blank.status_code == 422
    assert oversized.status_code == 422


def test_cors_allows_the_public_github_pages_frontend() -> None:
    response = client().options(
        "/v1/link",
        headers={
            "Origin": "https://ofeliacode.github.io",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://ofeliacode.github.io"
    )


def test_default_runtime_resolves_a_dirty_alias_from_demo_catalog() -> None:
    response = TestClient(
        create_app(service=LexicalLinkingService.from_catalog(DEFAULT_CATALOG))
    ).post(
        "/v1/link", json={"text": "ищу 15pm на 256"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "linked"
    assert body["selected_product"]["product_id"] == (
        "apple-iphone-15-pro-max-256-black"
    )
    assert body["processing_ms"] >= 0


class ConstantEncoder:
    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0] for _ in texts]


def test_end_to_end_service_combines_retrieval_reranking_and_versions() -> None:
    service = EndToEndLinkingService.from_catalog(
        DEFAULT_CATALOG,
        encoder=ConstantEncoder(),
    )

    result = service.analyze("ищу самсунь s24 ultra серый на 256")

    assert result.status == "linked"
    assert result.product_id == "samsung-galaxy-s24-ultra-256-gray"
    assert result.category == "smartphone"
    assert result.confidence == result.score
    assert result.decision_source == "feature_reranker"
    assert result.model_version == "feature-reranker-v0.1.0"
