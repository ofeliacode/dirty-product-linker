"""Import a bounded, pinned sample of the Shopify Product Catalogue."""

import argparse
from pathlib import Path

from dirty_product_linker.catalog.checkpoint import (
    ShopifyImportCheckpoint,
    load_import_checkpoint,
    run_checkpointed_import,
    save_import_checkpoint,
)
from dirty_product_linker.catalog.pipeline import stream_shopify_rows, write_shopify_result
from dirty_product_linker.catalog.taxonomy import TaxonomyMap


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000, help="Maximum source rows to read")
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1000,
        help="Atomically save state and print progress after this many source rows",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("reports/data/shopify_import_checkpoint.json"),
        help="Resumable cumulative import state",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from an existing checkpoint",
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=Path("configs/data/taxonomy.yaml"),
        help="Versioned external-to-project category mapping",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/shopify_catalog.jsonl"),
        help="Validated Product JSONL output",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/data/shopify_import.json"),
        help="Audit report output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    taxonomy = TaxonomyMap.from_yaml(args.taxonomy)
    if args.resume:
        if not args.checkpoint.exists():
            raise FileNotFoundError(f"checkpoint does not exist: {args.checkpoint}")
        initial = load_import_checkpoint(args.checkpoint)
    else:
        initial = ShopifyImportCheckpoint(source_rows_processed=0)
        save_import_checkpoint(args.checkpoint, initial)

    rows = stream_shopify_rows(
        limit=args.limit,
        skip=initial.source_rows_processed,
    )
    result = run_checkpointed_import(
        rows,
        taxonomy=taxonomy,
        checkpoint_path=args.checkpoint,
        checkpoint_every=args.checkpoint_every,
        initial=initial,
        on_progress=lambda read: print(f"Processed {read} source rows", flush=True),
    )
    write_shopify_result(result, catalog_path=args.output, report_path=args.report)
    print(
        f"Read {result.read}; accepted {result.accepted}; rejected {result.rejected}. "
        f"Report: {args.report}"
    )


if __name__ == "__main__":
    main()
