"""Freeze a manually approved multi-product candidate set as human-reviewed."""

import argparse
from pathlib import Path

from dirty_product_linker.benchmark.review import (
    promote_reviewed_multi_product_candidates,
)
from dirty_product_linker.schemas import MultiProductQuery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("data/benchmark/candidates/multi_product_v0_1.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/benchmark/frozen/multi_product_v0_1.jsonl"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/benchmark/frozen/multi_product_v0_1_manifest.json"),
    )
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reviewed-at", required=True, help="Review date in YYYY-MM-DD")
    parser.add_argument(
        "--confirm-all",
        action="store_true",
        help="Required acknowledgement that every query, link, and offset was reviewed",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_all:
        raise ValueError("--confirm-all is required after reviewing every annotation")
    queries = [
        MultiProductQuery.model_validate_json(line)
        for line in args.candidates.read_text(encoding="utf-8").splitlines()
        if line
    ]
    result = promote_reviewed_multi_product_candidates(
        queries=queries,
        reviewed_path=args.output,
        manifest_path=args.manifest,
        reviewer=args.reviewer,
        reviewed_at=args.reviewed_at,
    )
    print(
        f"Frozen {result.example_count} human-reviewed queries; "
        f"reviewed_sha256={result.reviewed_sha256}"
    )


if __name__ == "__main__":
    main()
