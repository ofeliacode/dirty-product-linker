"""Import a bounded, pinned sample of the Shopify Product Catalogue."""

import argparse
from pathlib import Path

from dirty_product_linker.catalog.pipeline import stream_shopify_rows, write_shopify_import
from dirty_product_linker.catalog.taxonomy import TaxonomyMap


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000, help="Maximum source rows to read")
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
    rows = stream_shopify_rows(limit=args.limit)
    result = write_shopify_import(
        rows,
        catalog_path=args.output,
        report_path=args.report,
        taxonomy=taxonomy,
    )
    print(
        f"Read {result.read}; accepted {result.accepted}; rejected {result.rejected}. "
        f"Report: {args.report}"
    )


if __name__ == "__main__":
    main()
