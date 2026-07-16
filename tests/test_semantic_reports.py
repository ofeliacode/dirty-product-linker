import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def load_report(name: str) -> dict[str, object]:
    path = PROJECT_ROOT / "reports/development" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_semantic_dense_report_compares_same_pinned_data_and_catalog() -> None:
    dataset = PROJECT_ROOT / "data/development/semantic_dev_v0_1.jsonl"
    catalog = PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"
    report = load_report("semantic_embedding_v0_1.json")

    assert report["dataset_role"] == "synthetic_development"
    assert report["dataset_sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert report["catalog_sha256"] == hashlib.sha256(catalog.read_bytes()).hexdigest()
    assert report["selection"]["threshold"] == 0.4  # type: ignore[index]
    assert report["metrics"]["overall"]["end_to_end_accuracy"] == 13 / 25  # type: ignore[index]
    assert report["lexical_comparison"]["metrics"]["overall"][  # type: ignore[index]
        "end_to_end_accuracy"
    ] == 6 / 25


def test_semantic_hybrid_report_records_one_dense_recovery() -> None:
    report = load_report("semantic_hybrid_v0_1.json")

    assert report["decision_source_counts"] == {  # type: ignore[index]
        "abstain": 21,
        "dense_fallback": 1,
        "lexical": 3,
    }
    assert report["metrics"]["overall"]["end_to_end_accuracy"] == 7 / 25  # type: ignore[index]
