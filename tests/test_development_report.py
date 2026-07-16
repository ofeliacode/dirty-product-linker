import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_development_report_matches_pinned_dataset_and_is_not_called_test() -> None:
    dataset_path = PROJECT_ROOT / "data/development/retrieval_dev_v0_1.jsonl"
    report = json.loads(
        (
            PROJECT_ROOT
            / "reports/development/lexical_development_v0_2.json"
        ).read_text(encoding="utf-8")
    )

    assert report["dataset_role"] == "synthetic_development"
    assert report["dataset_sha256"] == hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    assert report["settings"] == {"min_score": 0.42, "top_k": 5}
    assert report["metrics"]["overall"]["example_count"] == 24
    assert report["metrics"]["overall"]["end_to_end_accuracy"] == 1.0
    assert len(report["predictions"]) == 24
