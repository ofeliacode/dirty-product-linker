from dirty_product_linker.evaluation.baseline import (
    BenchmarkExample,
    evaluate_predictions,
)
from dirty_product_linker.linking.lexical import LinkCandidate, LinkResult
from dirty_product_linker.schemas import AnnotatedQuery


def example(
    query_id: str,
    *,
    slice_name: str,
    target_ids: list[str],
) -> BenchmarkExample:
    return BenchmarkExample(
        slice_name=slice_name,
        query=AnnotatedQuery.model_validate(
            {
                "query_id": query_id,
                "text": "query text",
                "language": "ru",
                "entities": [],
                "target_product_ids": target_ids,
                "answerable": bool(target_ids),
                "provenance": "human",
            }
        ),
    )


def linked(product_id: str, *candidate_ids: str) -> LinkResult:
    ids = (product_id, *candidate_ids)
    return LinkResult(
        status="linked",
        product_id=product_id,
        score=0.9,
        candidates=tuple(
            LinkCandidate(product_id=item, score=0.9, matched_surface=item)
            for item in ids
        ),
    )


def unknown(*candidate_ids: str) -> LinkResult:
    return LinkResult(
        status="unknown",
        product_id=None,
        score=0.2,
        candidates=tuple(
            LinkCandidate(product_id=item, score=0.2, matched_surface=item)
            for item in candidate_ids
        ),
    )


def test_metrics_distinguish_linking_recall_abstention_and_coverage() -> None:
    examples = [
        example("dirty-1", slice_name="dirty", target_ids=["phone-1"]),
        example("dirty-2", slice_name="dirty", target_ids=["phone-2"]),
        example("negative-1", slice_name="negative", target_ids=[]),
    ]
    predictions = {
        "dirty-1": linked("phone-1"),
        "dirty-2": unknown("phone-2"),
        "negative-1": unknown("phone-1"),
    }

    report = evaluate_predictions(examples, predictions)

    assert report.overall.accuracy_at_1 == 0.5
    assert report.overall.recall_at_5 == 1.0
    assert report.overall.negative_accuracy == 1.0
    assert report.overall.end_to_end_accuracy == 2 / 3
    assert report.overall.accepted_precision == 1.0
    assert report.overall.coverage == 1 / 3
    assert report.by_slice["dirty"].example_count == 2


def test_wrong_accepted_link_reduces_accepted_precision() -> None:
    examples = [
        example("dirty-1", slice_name="dirty", target_ids=["phone-1"]),
        example("dirty-2", slice_name="dirty", target_ids=["phone-2"]),
    ]
    predictions = {
        "dirty-1": linked("phone-1"),
        "dirty-2": linked("wrong-phone", "phone-2"),
    }

    report = evaluate_predictions(examples, predictions)

    assert report.overall.accuracy_at_1 == 0.5
    assert report.overall.recall_at_5 == 1.0
    assert report.overall.accepted_precision == 0.5
