"""Strict span and entity-linking metrics for multi-product extraction."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from dirty_product_linker.api.schemas import ExtractionResponse
from dirty_product_linker.schemas import MultiProductQuery


@dataclass(frozen=True, slots=True)
class MentionMetrics:
    """Aggregate exact-span and product-linking quality."""

    query_count: int
    gold_mention_count: int
    predicted_mention_count: int
    exact_span_precision: float
    exact_span_recall: float
    exact_span_f1: float
    linking_accuracy_on_exact_spans: float
    end_to_end_mention_accuracy: float
    query_exact_match: float
    negative_accuracy: float


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def evaluate_mentions(
    examples: Sequence[MultiProductQuery],
    predictions: Mapping[str, ExtractionResponse],
) -> MentionMetrics:
    """Evaluate immutable predictions against exact half-open gold spans."""

    if not examples:
        raise ValueError("examples cannot be empty")
    query_ids = [example.query_id for example in examples]
    if len(query_ids) != len(set(query_ids)):
        raise ValueError("examples contain duplicate query IDs")
    missing = set(query_ids) - set(predictions)
    if missing:
        raise ValueError(f"missing predictions for query IDs: {sorted(missing)}")

    gold_count = 0
    predicted_count = 0
    exact_span_matches = 0
    correct_links = 0
    exact_queries = 0
    negative_queries = 0
    correct_negatives = 0

    for example in examples:
        prediction = predictions[example.query_id]
        gold = {
            (mention.start, mention.end): mention.product_id
            for mention in example.mentions
        }
        predicted = {
            (mention.start, mention.end): mention.result.product_id
            for mention in prediction.mentions
        }
        gold_count += len(gold)
        predicted_count += len(predicted)
        shared_spans = set(gold) & set(predicted)
        exact_span_matches += len(shared_spans)
        correct_links += sum(gold[span] == predicted[span] for span in shared_spans)
        exact_queries += int(gold == predicted)
        if not gold:
            negative_queries += 1
            correct_negatives += int(not predicted)

    precision = _ratio(exact_span_matches, predicted_count)
    recall = _ratio(exact_span_matches, gold_count)
    return MentionMetrics(
        query_count=len(examples),
        gold_mention_count=gold_count,
        predicted_mention_count=predicted_count,
        exact_span_precision=precision,
        exact_span_recall=recall,
        exact_span_f1=_f1(precision, recall),
        linking_accuracy_on_exact_spans=_ratio(correct_links, exact_span_matches),
        end_to_end_mention_accuracy=_ratio(correct_links, gold_count),
        query_exact_match=_ratio(exact_queries, len(examples)),
        negative_accuracy=_ratio(correct_negatives, negative_queries),
    )
