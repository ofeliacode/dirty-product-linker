"""Development-only threshold selection for scored linker predictions."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from dirty_product_linker.evaluation.baseline import (
    BenchmarkExample,
    EvaluationReport,
    evaluate_predictions,
)
from dirty_product_linker.linking.lexical import LinkResult


@dataclass(frozen=True, slots=True)
class ThresholdSelection:
    """Best development threshold and the decisions it produced."""

    threshold: float
    report: EvaluationReport
    predictions: dict[str, LinkResult]


def apply_threshold(
    raw_predictions: Mapping[str, LinkResult],
    *,
    threshold: float,
) -> dict[str, LinkResult]:
    """Convert raw top-1 scores into linked or unknown decisions."""

    if not -1 <= threshold <= 1:
        raise ValueError("threshold must be between minus one and one")
    decisions: dict[str, LinkResult] = {}
    for query_id, prediction in raw_predictions.items():
        accepted = prediction.score >= threshold
        decisions[query_id] = LinkResult(
            status="linked" if accepted else "unknown",
            product_id=prediction.product_id if accepted else None,
            score=prediction.score,
            candidates=prediction.candidates,
        )
    return decisions


def select_threshold(
    examples: Sequence[BenchmarkExample],
    raw_predictions: Mapping[str, LinkResult],
    *,
    thresholds: Sequence[float],
) -> ThresholdSelection:
    """Select only on development data using a documented deterministic objective."""

    if not thresholds:
        raise ValueError("at least one threshold is required")
    selections: list[ThresholdSelection] = []
    for threshold in thresholds:
        predictions = apply_threshold(raw_predictions, threshold=threshold)
        selections.append(
            ThresholdSelection(
                threshold=threshold,
                report=evaluate_predictions(examples, predictions),
                predictions=predictions,
            )
        )

    return max(
        selections,
        key=lambda selection: (
            selection.report.overall.end_to_end_accuracy,
            selection.report.overall.accepted_precision,
            selection.report.overall.coverage,
            selection.threshold,
        ),
    )
