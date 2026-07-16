"""Build a deterministic catalog release from imported Product JSONL."""

import argparse
from pathlib import Path

from dirty_product_linker.catalog.release import build_release_from_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/data/catalog_v1.yaml"),
        help="Catalog release YAML configuration",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_release_from_config(args.config)
    counts = ", ".join(
        f"{category.value}={count}"
        for category, count in sorted(
            result.category_counts.items(),
            key=lambda item: item[0].value,
        )
    )
    print(
        f"Built {len(result.products)} products; removed "
        f"{result.duplicates_removed} duplicates; {counts}"
    )


if __name__ == "__main__":
    main()
