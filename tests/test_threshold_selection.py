from dirty_product_linker.evaluation.baseline import BenchmarkExample
from dirty_product_linker.evaluation.thresholds import select_threshold
from dirty_product_linker.linking.lexical import LinkCandidate, LinkResult
from dirty_product_linker.schemas import AnnotatedQuery


def example(query_id: str, targets: list[str]) -> BenchmarkExample:
    return BenchmarkExample(
        slice_name="answerable" if targets else "negative",
        query=AnnotatedQuery.model_validate(
            {
                "query_id": query_id,
                "text": query_id,
                "language": "ru",
                "entities": [],
                "target_product_ids": targets,
                "answerable": bool(targets),
                "provenance": "synthetic",
            }
        ),
    )


def raw_result(product_id: str, score: float) -> LinkResult:
    return LinkResult(
        status="linked",
        product_id=product_id,
        score=score,
        candidates=(
            LinkCandidate(
                product_id=product_id,
                score=score,
                matched_surface=product_id,
            ),
        ),
    )


def test_threshold_selection_balances_correct_links_and_negative_abstention() -> None:
    examples = [example("positive", ["phone-1"]), example("negative", [])]
    raw_predictions = {
        "positive": raw_result("phone-1", 0.7),
        "negative": raw_result("wrong-phone", 0.5),
    }

    selection = select_threshold(
        examples,
        raw_predictions,
        thresholds=[0.4, 0.6, 0.8],
    )

    assert selection.threshold == 0.6
    assert selection.report.overall.end_to_end_accuracy == 1.0
    assert selection.report.overall.coverage == 0.5
