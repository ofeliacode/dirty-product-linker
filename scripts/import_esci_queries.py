"""Import a bounded, pinned sample of Amazon ESCI training judgments."""

import argparse
from pathlib import Path

from dirty_product_linker.catalog.esci_pipeline import (
    stream_esci_rows,
    write_esci_import,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000, help="Maximum source rows to read")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/esci_train_judgments.jsonl"),
        help="Validated QueryProductJudgment JSONL output",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/data/esci_train_import.json"),
        help="Audit report output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    split = "train"
    result = write_esci_import(
        stream_esci_rows(limit=args.limit, split=split),
        output_path=args.output,
        report_path=args.report,
        requested_split=split,
    )
    print(
        f"Read {result.read}; accepted {result.accepted}; rejected {result.rejected}. "
        f"Report: {args.report}"
    )


if __name__ == "__main__":
    main()
