import hashlib
import json
from pathlib import Path

from dirty_product_linker.schemas import MultiProductQuery

PROJECT_ROOT = Path(__file__).parents[1]


def test_reviewed_report_is_bound_to_human_attestation_and_frozen_data() -> None:
    dataset = PROJECT_ROOT / "data/benchmark/frozen/multi_product_v0_1.jsonl"
    manifest_path = (
        PROJECT_ROOT / "data/benchmark/frozen/multi_product_v0_1_manifest.json"
    )
    report = json.loads(
        (
            PROJECT_ROOT / "reports/evaluation/multi_product_reviewed_v0_1.json"
        ).read_text(encoding="utf-8")
    )
    rows = [
        MultiProductQuery.model_validate_json(line)
        for line in dataset.read_text(encoding="utf-8").splitlines()
    ]

    assert report["dataset_role"] == "human_reviewed_synthetic_origin"
    assert report["dataset_sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert report["manifest_sha256"] == hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
    assert report["review"]["reviewer"] == "ofeliacode"
    assert report["review"]["reviewed_sha256"] == report["dataset_sha256"]
    assert all(row.provenance == "human" for row in rows)
    assert report["metrics"]["overall"]["exact_span_f1"] == 10 / 11
    assert report["metrics"]["overall"]["end_to_end_mention_accuracy"] == 25 / 30
    assert report["metrics"]["by_slice"]["unseen_surface"][
        "exact_span_recall"
    ] == 0.0
