import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_multi_product_report_is_pinned_and_clearly_candidate_only() -> None:
    dataset = PROJECT_ROOT / "data/benchmark/candidates/multi_product_v0_1.jsonl"
    catalog = PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"
    report = json.loads(
        (
            PROJECT_ROOT / "reports/development/multi_product_candidates_v0_1.json"
        ).read_text(encoding="utf-8")
    )

    assert report["dataset_role"] == "synthetic_candidate"
    assert report["dataset_sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert report["catalog_sha256"] == hashlib.sha256(catalog.read_bytes()).hexdigest()
    assert report["metrics"]["overall"] == {
        "query_count": 25,
        "gold_mention_count": 30,
        "predicted_mention_count": 25,
        "exact_span_precision": 1.0,
        "exact_span_recall": 25 / 30,
        "exact_span_f1": 10 / 11,
        "linking_accuracy_on_exact_spans": 1.0,
        "end_to_end_mention_accuracy": 25 / 30,
        "query_exact_match": 0.8,
        "negative_accuracy": 1.0,
    }
    assert report["metrics"]["by_slice"]["unseen_surface"][
        "exact_span_recall"
    ] == 0.0
    assert len(report["predictions"]) == 25
