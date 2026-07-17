from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from dirty_product_linker.schemas import MultiProductQuery, Product

PROJECT_ROOT = Path(__file__).parents[1]
DATASET_PATH = PROJECT_ROOT / "data/benchmark/candidates/ai_challenge_v0_1.jsonl"
CATALOG_PATH = PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_ai_challenge_has_requested_slice_distribution_and_valid_labels() -> None:
    rows = [MultiProductQuery.model_validate(row) for row in load_jsonl(DATASET_PATH)]
    products = [Product.model_validate(row) for row in load_jsonl(CATALOG_PATH)]
    catalog_ids = {product.product_id for product in products}

    assert len(rows) == 100
    assert len({row.query_id for row in rows}) == 100
    assert Counter(row.slice_name for row in rows) == {
        "ordinary_single": 20,
        "slang_and_typos": 20,
        "multi_product": 20,
        "ambiguous": 15,
        "negative": 15,
        "unseen_abbreviation": 10,
    }
    assert all(row.provenance.value == "synthetic" for row in rows)

    for row in rows:
        for mention in row.mentions:
            assert row.text[mention.start : mention.end] == mention.text
            assert mention.product_id in catalog_ids


def test_ai_challenge_special_slices_have_expected_behavior() -> None:
    rows = [MultiProductQuery.model_validate(row) for row in load_jsonl(DATASET_PATH)]
    by_slice: dict[str, list[MultiProductQuery]] = {}
    for row in rows:
        by_slice.setdefault(row.slice_name, []).append(row)

    assert all(len(row.mentions) == 1 for row in by_slice["ordinary_single"])
    assert all(len(row.mentions) == 1 for row in by_slice["slang_and_typos"])
    assert all(len(row.mentions) >= 2 for row in by_slice["multi_product"])
    assert all(not row.mentions for row in by_slice["negative"])
    assert all(len(row.mentions) == 1 for row in by_slice["unseen_abbreviation"])
