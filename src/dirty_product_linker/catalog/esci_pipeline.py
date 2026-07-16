"""Streaming and serialization boundary for Amazon ESCI judgments."""

import json
from collections.abc import Iterable, Iterator, Mapping
from importlib import import_module
from itertools import islice
from pathlib import Path
from typing import Any

from dirty_product_linker.catalog.esci import (
    SOURCE_ID,
    SOURCE_REVISION,
    EsciImportResult,
    import_esci_records,
)

SOURCE_CONFIG = "queries"


def stream_esci_rows(
    *,
    limit: int,
    split: str = "train",
) -> Iterator[Mapping[str, object]]:
    """Stream a bounded sample from the pinned ESCI query configuration."""

    if limit < 1:
        raise ValueError("limit must be at least 1")
    if split != "train":
        raise ValueError("only the train split can be imported into development data")

    try:
        datasets_module = import_module("datasets")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Hugging Face data support is not installed; run pip install -e '.[data]'"
        ) from error

    load_dataset: Any = datasets_module.load_dataset
    dataset: Iterable[Mapping[str, object]] = load_dataset(
        SOURCE_ID,
        name=SOURCE_CONFIG,
        split=split,
        revision=SOURCE_REVISION,
        streaming=True,
    )
    yield from islice(dataset, limit)


def write_esci_import(
    records: Iterable[Mapping[str, object]],
    *,
    output_path: Path,
    report_path: Path,
    requested_split: str,
) -> EsciImportResult:
    """Validate and atomically write ESCI judgments with an audit report."""

    result = import_esci_records(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_output = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary_output.open("w", encoding="utf-8") as output:
        for judgment in result.judgments:
            output.write(judgment.model_dump_json() + "\n")
    temporary_output.replace(output_path)

    report = {
        "schema_version": "1.0",
        "dataset_id": SOURCE_ID,
        "source_config": SOURCE_CONFIG,
        "revision": SOURCE_REVISION,
        "requested_split": requested_split,
        "read": result.read,
        "accepted": result.accepted,
        "rejected": result.rejected,
        "rejection_reasons": result.rejection_reasons,
    }
    temporary_report = report_path.with_suffix(report_path.suffix + ".tmp")
    temporary_report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_report.replace(report_path)
    return result
