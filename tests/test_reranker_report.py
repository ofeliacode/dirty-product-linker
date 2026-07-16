import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_reranker_report_is_pinned_explainable_and_development_only() -> None:
    dataset = PROJECT_ROOT / "data/development/semantic_dev_v0_1.jsonl"
    catalog = PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"
    report = json.loads(
        (
            PROJECT_ROOT / "reports/development/semantic_reranker_v0_1.json"
        ).read_text(encoding="utf-8")
    )

    assert report["dataset_role"] == "synthetic_development"
    assert report["dataset_sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert report["catalog_sha256"] == hashlib.sha256(catalog.read_bytes()).hexdigest()
    assert report["policy"]["min_score"] == 0.4
    assert report["policy"]["min_margin"] == 0.08
    assert report["decision_source_counts"] == {
        "abstain_low_score": 2,
        "abstain_no_identity": 5,
        "feature_reranker": 18,
    }
    assert report["metrics"]["overall"]["end_to_end_accuracy"] == 23 / 25
    assert report["metrics"]["overall"]["accepted_precision"] == 1.0
    assert len(report["predictions"]) == 25
    assert all(
        prediction["features_by_product"] for prediction in report["predictions"]
    )
