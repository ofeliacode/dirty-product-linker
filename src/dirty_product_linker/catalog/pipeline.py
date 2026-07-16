"""I/O boundary for streaming and writing the Shopify catalog import."""

import json
from collections.abc import Callable, Iterable, Iterator, Mapping
from importlib import import_module
from itertools import islice
from pathlib import Path
from typing import Any

from dirty_product_linker.catalog.shopify import (
    SOURCE_ID,
    SOURCE_REVISION,
    ShopifyImportResult,
    import_shopify_records,
)
from dirty_product_linker.catalog.taxonomy import TaxonomyMap

SOURCE_COLUMNS = [
    "product_title",
    "product_description",
    "ground_truth_brand",
    "ground_truth_category",
    "ground_truth_is_secondhand",
]


def stream_shopify_rows(*, limit: int, split: str = "train") -> Iterator[Mapping[str, object]]:
    """Stream a pinned public dataset revision without downloading it in full."""

    if limit < 1:
        raise ValueError("limit must be at least 1")

    try:
        datasets_module = import_module("datasets")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Hugging Face data support is not installed; run pip install -e '.[data]'"
        ) from error

    # API reference: https://huggingface.co/docs/datasets/package_reference/loading_methods#datasets.load_dataset
    load_dataset: Any = datasets_module.load_dataset
    dataset: Any = load_dataset(
        SOURCE_ID,
        split=split,
        revision=SOURCE_REVISION,
        streaming=True,
    )
    # Selecting before iteration prevents decoding the unused image column.
    # Reference: https://huggingface.co/docs/datasets/package_reference/main_classes#datasets.IterableDataset.select_columns
    selected_dataset: Iterable[Mapping[str, object]] = dataset.select_columns(SOURCE_COLUMNS)
    yield from islice(selected_dataset, limit)


def write_shopify_import(
    records: Iterable[Mapping[str, object]],
    *,
    catalog_path: Path,
    report_path: Path,
    taxonomy: TaxonomyMap,
    progress_every: int = 1000,
    on_progress: Callable[[int], None] | None = None,
) -> ShopifyImportResult:
    """Validate source rows and atomically describe what was accepted or rejected."""

    result = import_shopify_records(
        records,
        taxonomy=taxonomy,
        progress_every=progress_every,
        on_progress=on_progress,
    )
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with catalog_path.open("w", encoding="utf-8") as output:
        for product in result.products:
            output.write(product.model_dump_json() + "\n")

    report = {
        "schema_version": "1.0",
        "dataset_id": SOURCE_ID,
        "revision": SOURCE_REVISION,
        "read": result.read,
        "accepted": result.accepted,
        "rejected": result.rejected,
        "rejection_reasons": result.rejection_reasons,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result
