"""Freeze manually reviewed benchmark slices and write an integrity manifest."""

import argparse
from pathlib import Path

from dirty_product_linker.benchmark.freeze import freeze_benchmark
from dirty_product_linker.schemas import AnnotatedQuery, Product


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reviewed-dir",
        type=Path,
        default=Path("data/benchmark/reviewed"),
        help="Directory containing one human-reviewed JSONL file per slice",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("data/catalog/sample_catalog.jsonl"),
        help="Catalog defining valid target product IDs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/benchmark/frozen/ru_dirty_v0_1.jsonl"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/benchmark/frozen/ru_dirty_v0_1_manifest.json"),
    )
    parser.add_argument("--version", default="ru-dirty-v0.1")
    return parser.parse_args()


def _read_queries(path: Path) -> list[AnnotatedQuery]:
    with path.open(encoding="utf-8") as source:
        return [
            AnnotatedQuery.model_validate_json(line)
            for line in source
            if line.strip()
        ]


def _read_products(path: Path) -> list[Product]:
    with path.open(encoding="utf-8") as source:
        return [Product.model_validate_json(line) for line in source if line.strip()]


def main() -> None:
    args = parse_args()
    slice_paths = sorted(args.reviewed_dir.glob("*.jsonl"))
    if not slice_paths:
        raise FileNotFoundError(
            f"no reviewed slices found in {args.reviewed_dir}; "
            "review candidates before freezing"
        )

    result = freeze_benchmark(
        slices={path.stem: _read_queries(path) for path in slice_paths},
        catalog=_read_products(args.catalog),
        output_path=args.output,
        manifest_path=args.manifest,
        benchmark_version=args.version,
    )
    print(
        f"Frozen {result.example_count} examples; sha256={result.sha256}; "
        f"manifest: {args.manifest}"
    )


if __name__ == "__main__":
    main()
