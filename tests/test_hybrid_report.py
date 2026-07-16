import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_hybrid_report_is_development_only_and_records_decision_paths() -> None:
    dataset_path = PROJECT_ROOT / "data/development/retrieval_dev_v0_1.jsonl"
    report = json.loads(
        (
            PROJECT_ROOT / "reports/development/hybrid_development_v0_1.json"
        ).read_text(encoding="utf-8")
    )

    assert report["dataset_role"] == "synthetic_development"
    assert report["dataset_sha256"] == hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    assert report["model"]["revision"] == (
        "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
    )
    assert report["policy"] == {
        "dense_min_margin": 0.12,
        "dense_min_score": 0.65,
        "lexical_min_score": 0.42,
        "lexical_support_score": 0.15,
    }
    assert report["decision_source_counts"] == {"abstain": 6, "lexical": 18}
    assert report["metrics"]["overall"]["end_to_end_accuracy"] == 1.0
    assert len(report["predictions"]) == 24
