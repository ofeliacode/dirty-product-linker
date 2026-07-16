"""Atomic checkpoint state for resumable Shopify imports."""

from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dirty_product_linker.catalog.shopify import (
    SOURCE_ID,
    SOURCE_REVISION,
    ShopifyImportResult,
    ShopifyRecordRejected,
    convert_shopify_record,
)
from dirty_product_linker.catalog.taxonomy import TaxonomyMap
from dirty_product_linker.schemas import Product


class ShopifyImportCheckpoint(BaseModel):
    """One self-contained, atomically replaceable import state."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    dataset_id: str = SOURCE_ID
    revision: str = SOURCE_REVISION
    split: str = "train"
    source_rows_processed: int = Field(ge=0)
    products: list[Product] = Field(default_factory=list)
    rejection_reasons: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_counts_and_identity(self) -> "ShopifyImportCheckpoint":
        rejected = sum(self.rejection_reasons.values())
        if self.source_rows_processed != len(self.products) + rejected:
            raise ValueError("checkpoint counts do not add up")
        if self.dataset_id != SOURCE_ID or self.revision != SOURCE_REVISION:
            raise ValueError("checkpoint source or revision does not match the importer")
        if self.split != "train":
            raise ValueError("checkpoint split does not match the importer")
        return self


def save_import_checkpoint(path: Path, checkpoint: ShopifyImportCheckpoint) -> None:
    """Atomically replace a checkpoint with validated JSON state."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_text(checkpoint.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def load_import_checkpoint(path: Path) -> ShopifyImportCheckpoint:
    """Load a checkpoint and reject stale or internally inconsistent state."""

    return ShopifyImportCheckpoint.model_validate_json(path.read_text(encoding="utf-8"))


def run_checkpointed_import(
    records: Iterable[Mapping[str, object]],
    *,
    taxonomy: TaxonomyMap,
    checkpoint_path: Path,
    checkpoint_every: int,
    initial: ShopifyImportCheckpoint | None = None,
    on_progress: Callable[[int], None] | None = None,
) -> ShopifyImportResult:
    """Process new rows and atomically persist cumulative state in bounded intervals."""

    if checkpoint_every < 1:
        raise ValueError("checkpoint_every must be at least 1")

    products = list(initial.products) if initial is not None else []
    rejection_reasons = Counter(initial.rejection_reasons if initial is not None else {})
    read = initial.source_rows_processed if initial is not None else 0
    since_checkpoint = 0

    for record in records:
        read += 1
        since_checkpoint += 1
        try:
            products.append(convert_shopify_record(record, taxonomy=taxonomy))
        except ShopifyRecordRejected as error:
            rejection_reasons[error.reason] += 1

        if since_checkpoint == checkpoint_every:
            checkpoint = ShopifyImportCheckpoint(
                source_rows_processed=read,
                products=products,
                rejection_reasons=dict(sorted(rejection_reasons.items())),
            )
            save_import_checkpoint(checkpoint_path, checkpoint)
            since_checkpoint = 0
            if on_progress is not None:
                on_progress(read)

    checkpoint = ShopifyImportCheckpoint(
        source_rows_processed=read,
        products=products,
        rejection_reasons=dict(sorted(rejection_reasons.items())),
    )
    save_import_checkpoint(checkpoint_path, checkpoint)
    return ShopifyImportResult(
        read=read,
        products=tuple(products),
        rejection_reasons=checkpoint.rejection_reasons,
    )
