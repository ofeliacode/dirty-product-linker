from fastapi.testclient import TestClient

from dirty_product_linker.api.app import create_app
from dirty_product_linker.api.schemas import (
    AnalysisResponse,
    CandidateResponse,
    ProductSummary,
)


class StubService:
    def analyze(self, text: str) -> AnalysisResponse:
        return AnalysisResponse(
            text=text,
            status="linked",
            decision_source="lexical",
            score=0.88,
            processing_ms=0.12,
            catalog_version="demo-catalog-v0.2",
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
    assert body["catalog_version"] == "demo-catalog-v0.2"


def test_link_endpoint_rejects_blank_or_oversized_text() -> None:
    blank = client().post("/v1/link", json={"text": "   "})
    oversized = client().post("/v1/link", json={"text": "x" * 501})

    assert blank.status_code == 422
    assert oversized.status_code == 422


def test_default_runtime_resolves_a_dirty_alias_from_demo_catalog() -> None:
    response = TestClient(create_app()).post(
        "/v1/link", json={"text": "ищу 15pm на 256"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "linked"
    assert body["selected_product"]["product_id"] == (
        "apple-iphone-15-pro-max-256-black"
    )
    assert body["processing_ms"] >= 0
