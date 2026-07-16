import json
from pathlib import Path

import pytest
import yaml

from dirty_product_linker.catalog.esci import (
    EsciRecordRejected,
    convert_esci_record,
    import_esci_records,
)
from dirty_product_linker.schemas import EsciLabel

PROJECT_ROOT = Path(__file__).parents[1]


def load_fixture_rows() -> list[dict[str, object]]:
    path = PROJECT_ROOT / "tests/fixtures/esci_queries.jsonl"
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def test_source_registry_records_origin_mirror_and_data_boundaries() -> None:
    with (PROJECT_ROOT / "configs/data/sources.yaml").open(encoding="utf-8") as source:
        registry = yaml.safe_load(source)

    esci = registry["sources"]["amazon_esci_queries"]
    assert esci["revision"] == "3bf15ee2b5c6483fc3b96f8656d0989bf33a18b5"
    assert esci["license"] == "apache-2.0"
    assert esci["origin"] == "https://github.com/amazon-science/esci-data"
    assert "product_taxonomy_ground_truth" in esci["prohibited_purposes"]


def test_esci_record_becomes_a_versioned_judgment() -> None:
    judgment = convert_esci_record(load_fixture_rows()[0])

    assert judgment.query == "iphone 15 pro max"
    assert judgment.label is EsciLabel.EXACT
    assert judgment.locale == "us"
    assert judgment.source_split == "train"


def test_test_split_is_preserved_instead_of_silently_becoming_training_data() -> None:
    row = {**load_fixture_rows()[0], "split": "test"}

    judgment = convert_esci_record(row)

    assert judgment.source_split == "test"


def test_invalid_source_split_is_rejected() -> None:
    row = {**load_fixture_rows()[0], "split": "validation"}

    with pytest.raises(EsciRecordRejected, match="invalid_split"):
        convert_esci_record(row)


def test_import_reports_dirty_rows_by_reason() -> None:
    result = import_esci_records(load_fixture_rows())

    assert result.read == 4
    assert result.accepted == 2
    assert result.rejected == 2
    assert result.rejection_reasons == {"invalid_locale": 1, "missing_query": 1}
