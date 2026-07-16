"""Record human approval of candidate benchmark slices."""

import argparse
from pathlib import Path

from dirty_product_linker.benchmark.review import promote_reviewed_candidates
from dirty_product_linker.schemas import AnnotatedQuery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates-dir",
        type=Path,
        default=Path("data/benchmark/candidates"),
    )
    parser.add_argument(
        "--reviewed-dir",
        type=Path,
        default=Path("data/benchmark/reviewed"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/benchmark/reviewed/review_manifest.json"),
    )
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reviewed-at", required=True, help="Review date in YYYY-MM-DD")
    parser.add_argument(
        "--confirm-all",
        action="store_true",
        help="Required acknowledgement that every candidate was reviewed",
    )
    return parser.parse_args()


def _read_queries(path: Path) -> list[AnnotatedQuery]:
    with path.open(encoding="utf-8") as source:
        return [
            AnnotatedQuery.model_validate_json(line)
            for line in source
            if line.strip()
        ]


def main() -> None:
    args = parse_args()
    if not args.confirm_all:
        raise ValueError("--confirm-all is required after reviewing every candidate")
    candidate_paths = sorted(args.candidates_dir.glob("*.jsonl"))
    if not candidate_paths:
        raise FileNotFoundError(f"no candidates found in {args.candidates_dir}")

    result = promote_reviewed_candidates(
        slices={path.stem: _read_queries(path) for path in candidate_paths},
        reviewed_dir=args.reviewed_dir,
        manifest_path=args.manifest,
        reviewer=args.reviewer,
        reviewed_at=args.reviewed_at,
    )
    print(
        f"Promoted {result.example_count} reviewed examples; "
        f"candidate_sha256={result.candidate_sha256}"
    )


if __name__ == "__main__":
    main()
