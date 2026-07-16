import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_embedding_report_is_pinned_and_development_only() -> None:
    dataset_path = PROJECT_ROOT / "data/development/retrieval_dev_v0_1.jsonl"
    report = json.loads(
        (
            PROJECT_ROOT
            / "reports/development/embedding_development_v0_1.json"
        ).read_text(encoding="utf-8")
    )

    assert report["dataset_role"] == "synthetic_development"
    assert report["dataset_sha256"] == hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    assert report["model"]["revision"] == (
        "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
    )
    assert report["model"]["license"] == "apache-2.0"
    assert report["selection"]["threshold"] == 0.4
    assert report["metrics"]["overall"]["end_to_end_accuracy"] == 20 / 24
    assert report["lexical_comparison"]["metrics"]["overall"][
        "end_to_end_accuracy"
    ] == 1.0
    assert len(report["predictions"]) == 24
