import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dirty_product_linker.catalog.esci_pipeline import (
    stream_esci_rows,
    write_esci_import,
)
from dirty_product_linker.schemas import QueryProductJudgment

PROJECT_ROOT = Path(__file__).parents[1]


def load_fixture_rows() -> list[dict[str, object]]:
    path = PROJECT_ROOT / "tests/fixtures/esci_queries.jsonl"
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def test_pipeline_writes_judgments_and_an_audit_report(tmp_path: Path) -> None:
    output_path = tmp_path / "judgments.jsonl"
    report_path = tmp_path / "report.json"

    result = write_esci_import(
        load_fixture_rows(),
        output_path=output_path,
        report_path=report_path,
        requested_split="train",
    )

    with output_path.open(encoding="utf-8") as source:
        judgments = [
            QueryProductJudgment.model_validate_json(line)
            for line in source
            if line.strip()
        ]
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert len(judgments) == 2
    assert result.accepted == 2
    assert report["accepted"] == 2
    assert report["source_config"] == "queries"
    assert report["requested_split"] == "train"
    assert report["rejection_reasons"] == {"invalid_locale": 1, "missing_query": 1}


def test_stream_uses_pinned_query_config_and_streaming(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = load_fixture_rows()
    load_arguments: dict[str, object] = {}

    def fake_load_dataset(dataset_id: str, **kwargs: object) -> list[dict[str, object]]:
        load_arguments.update({"dataset_id": dataset_id, **kwargs})
        return rows

    monkeypatch.setattr(
        "dirty_product_linker.catalog.esci_pipeline.import_module",
        lambda _: SimpleNamespace(load_dataset=fake_load_dataset),
    )

    streamed = list(stream_esci_rows(limit=2, split="train"))

    assert len(streamed) == 2
    assert load_arguments == {
        "dataset_id": "milistu/amazon-esci-data",
        "name": "queries",
        "split": "train",
        "revision": "3bf15ee2b5c6483fc3b96f8656d0989bf33a18b5",
        "streaming": True,
    }


def test_stream_rejects_non_train_split_by_default() -> None:
    with pytest.raises(ValueError, match="only the train split"):
        list(stream_esci_rows(limit=1, split="test"))
