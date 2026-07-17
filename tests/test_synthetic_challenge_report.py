import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_synthetic_challenge_baseline_is_pinned_and_reproducible() -> None:
    dataset = (
        PROJECT_ROOT / "data/benchmark/candidates/synthetic_challenge_v0_1.jsonl"
    )
    catalog = PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"
    report = json.loads(
        (
            PROJECT_ROOT
            / "reports/development/synthetic_challenge_v0_1_baseline.json"
        ).read_text(encoding="utf-8")
    )

    assert report["dataset_role"] == "synthetic_blind_challenge"
    assert report["dataset_sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert report["catalog_sha256"] == hashlib.sha256(catalog.read_bytes()).hexdigest()
    assert report["metrics"]["overall"] == {
        "query_count": 100,
        "gold_mention_count": 103,
        "predicted_mention_count": 48,
        "exact_span_precision": 46 / 48,
        "exact_span_recall": 46 / 103,
        "exact_span_f1": 0.6092715231788081,
        "linking_accuracy_on_exact_spans": 1.0,
        "end_to_end_mention_accuracy": 46 / 103,
        "query_exact_match": 0.51,
        "negative_accuracy": 1.0,
    }
    assert report["metrics"]["by_slice"]["ordinary_single"][
        "end_to_end_mention_accuracy"
    ] == 0.95
    assert report["metrics"]["by_slice"]["slang_and_typos"][
        "end_to_end_mention_accuracy"
    ] == 0.0
    assert report["metrics"]["by_slice"]["unseen_abbreviation"][
        "end_to_end_mention_accuracy"
    ] == 0.0
    assert len(report["predictions"]) == 100
