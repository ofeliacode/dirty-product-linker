import pytest

from dirty_product_linker.api.schemas import AnalysisResponse, ProductSummary
from dirty_product_linker.cli import main


class StubService:
    def analyze(self, text: str) -> AnalysisResponse:
        product = ProductSummary(
            product_id="apple-iphone-15-pro-max-256-black",
            brand="Apple",
            model="iPhone 15 Pro Max",
            category="smartphone",
        )
        return AnalysisResponse(
            text=text,
            status="linked",
            decision_source="feature_reranker",
            score=0.87,
            confidence=0.87,
            processing_ms=12.4,
            model_version="feature-reranker-v0.1.1",
            catalog_version="demo-catalog-v0.2",
            product_id=product.product_id,
            category=product.category,
            selected_product=product,
            candidates=[],
        )


def test_predict_command_prints_machine_readable_versioned_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["predict", "хочу 15pm на 256"],
        service=StubService(),
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"product_id": "apple-iphone-15-pro-max-256-black"' in output
    assert '"confidence": 0.87' in output
    assert '"model_version": "feature-reranker-v0.1.1"' in output
