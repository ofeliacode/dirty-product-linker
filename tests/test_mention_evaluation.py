import pytest

from dirty_product_linker.api.schemas import AnalysisResponse, ExtractionResponse, LinkedMention
from dirty_product_linker.evaluation.mentions import evaluate_mentions
from dirty_product_linker.schemas import MultiProductQuery


def example(query_id: str, text: str, mentions: list[dict[str, object]]) -> MultiProductQuery:
    return MultiProductQuery.model_validate(
        {
            "query_id": query_id,
            "text": text,
            "language": "ru-mixed",
            "slice_name": "multi",
            "mentions": mentions,
            "provenance": "synthetic",
        }
    )


def linked(text: str, start: int, end: int, product_id: str) -> LinkedMention:
    return LinkedMention(
        text=text[start:end],
        start=start,
        end=end,
        result=AnalysisResponse(
            text=text[start:end],
            status="linked",
            decision_source="test",
            score=1,
            confidence=1,
            processing_ms=0,
            model_version="test",
            catalog_version="test",
            product_id=product_id,
        ),
    )


def test_reports_span_linking_end_to_end_and_negative_metrics_separately() -> None:
    first = example(
        "multi-1",
        "alpha и beta",
        [
            {"start": 0, "end": 5, "text": "alpha", "product_id": "product-a"},
            {"start": 8, "end": 12, "text": "beta", "product_id": "product-b"},
        ],
    )
    negative = example("negative-1", "просто совет", [])
    predictions = {
        "multi-1": ExtractionResponse(
            text=first.text,
            mentions=[
                linked(first.text, 0, 5, "product-a"),
                linked(first.text, 8, 12, "wrong-product"),
            ],
        ),
        "negative-1": ExtractionResponse(text=negative.text),
    }

    report = evaluate_mentions([first, negative], predictions)

    assert report.exact_span_precision == 1
    assert report.exact_span_recall == 1
    assert report.exact_span_f1 == 1
    assert report.linking_accuracy_on_exact_spans == 0.5
    assert report.end_to_end_mention_accuracy == 0.5
    assert report.query_exact_match == 0.5
    assert report.negative_accuracy == 1


def test_rejects_missing_predictions() -> None:
    row = example("multi-1", "alpha", [])

    with pytest.raises(ValueError, match="missing predictions"):
        evaluate_mentions([row], {})
