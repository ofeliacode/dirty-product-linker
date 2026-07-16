import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_committed_baseline_report_matches_frozen_benchmark_and_settings() -> None:
    benchmark_path = PROJECT_ROOT / "data/benchmark/frozen/ru_dirty_v0_1.jsonl"
    report_path = PROJECT_ROOT / "reports/evaluation/lexical_baseline_v0_1.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["benchmark_sha256"] == hashlib.sha256(
        benchmark_path.read_bytes()
    ).hexdigest()
    assert report["settings"] == {"min_score": 0.42, "top_k": 5}
    assert report["metrics"]["overall"]["example_count"] == 20
    assert report["metrics"]["overall"]["accuracy_at_1"] == 11 / 15
    assert report["metrics"]["overall"]["end_to_end_accuracy"] == 0.8
    assert len(report["predictions"]) == 20
