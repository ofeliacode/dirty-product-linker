"""Pure metric calculations for product-linking benchmark predictions."""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from dirty_product_linker.linking.lexical import LinkResult
from dirty_product_linker.schemas import AnnotatedQuery


@dataclass(frozen=True, slots=True)
class BenchmarkExample:
    """One reviewed query plus its frozen evaluation slice."""

    slice_name: str
    query: AnnotatedQuery


@dataclass(frozen=True, slots=True)
class SliceMetrics:
    """Linking and abstention metrics for one group of examples."""

    example_count: int
    answerable_count: int
    negative_count: int
    accuracy_at_1: float
    recall_at_5: float
    negative_accuracy: float
    end_to_end_accuracy: float
    accepted_precision: float
    coverage: float


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Overall metrics and the same metrics broken down by benchmark slice."""

    overall: SliceMetrics
    by_slice: dict[str, SliceMetrics]


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _calculate_metrics(
    examples: Sequence[BenchmarkExample],
    predictions: Mapping[str, LinkResult],
) -> SliceMetrics:
    answerable = 0
    negatives = 0
    correct_top_1 = 0
    recalled_top_5 = 0
    correct_negatives = 0
    correct_end_to_end = 0
    accepted = 0
    correct_accepted = 0

    for example in examples:
        query = example.query
        prediction = predictions[query.query_id]
        targets = set(query.target_product_ids)
        candidate_ids = {candidate.product_id for candidate in prediction.candidates[:5]}
        is_accepted = prediction.status == "linked"
        if is_accepted:
            accepted += 1

        if query.answerable:
            answerable += 1
            top_1_correct = prediction.product_id in targets
            recall_correct = bool(candidate_ids & targets)
            correct_top_1 += int(top_1_correct)
            recalled_top_5 += int(recall_correct)
            correct_end_to_end += int(top_1_correct)
            correct_accepted += int(is_accepted and top_1_correct)
        else:
            negatives += 1
            abstained = prediction.status == "unknown"
            correct_negatives += int(abstained)
            correct_end_to_end += int(abstained)

    return SliceMetrics(
        example_count=len(examples),
        answerable_count=answerable,
        negative_count=negatives,
        accuracy_at_1=_ratio(correct_top_1, answerable),
        recall_at_5=_ratio(recalled_top_5, answerable),
        negative_accuracy=_ratio(correct_negatives, negatives),
        end_to_end_accuracy=_ratio(correct_end_to_end, len(examples)),
        accepted_precision=_ratio(correct_accepted, accepted),
        coverage=_ratio(accepted, len(examples)),
    )


def evaluate_predictions(
    examples: Sequence[BenchmarkExample],
    predictions: Mapping[str, LinkResult],
) -> EvaluationReport:
    """Calculate fixed metrics without modifying predictions or thresholds."""

    if not examples:
        raise ValueError("examples cannot be empty")
    query_ids = [example.query.query_id for example in examples]
    if len(set(query_ids)) != len(query_ids):
        raise ValueError("benchmark contains duplicate query IDs")
    missing = set(query_ids) - set(predictions)
    if missing:
        raise ValueError(f"missing predictions for query IDs: {sorted(missing)}")

    grouped: defaultdict[str, list[BenchmarkExample]] = defaultdict(list)
    for example in examples:
        grouped[example.slice_name].append(example)

    return EvaluationReport(
        overall=_calculate_metrics(examples, predictions),
        by_slice={
            slice_name: _calculate_metrics(grouped[slice_name], predictions)
            for slice_name in sorted(grouped)
        },
    )
