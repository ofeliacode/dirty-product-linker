import json
from collections import Counter
from pathlib import Path

from dirty_product_linker.schemas import MultiProductQuery, Product

PROJECT_ROOT = Path(__file__).parents[1]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_multi_product_candidates_are_valid_synthetic_and_catalog_bound() -> None:
    rows = [
        MultiProductQuery.model_validate(row)
        for row in read_jsonl(
            PROJECT_ROOT / "data/benchmark/candidates/multi_product_v0_1.jsonl"
        )
    ]
    catalog_ids = {
        Product.model_validate(row).product_id
        for row in read_jsonl(PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl")
    }

    assert len(rows) == 25
    assert len({row.query_id for row in rows}) == len(rows)
    assert all(row.provenance == "synthetic" for row in rows)
    assert Counter(row.slice_name for row in rows) == {
        "explicit_alias": 10,
        "context": 5,
        "unseen_surface": 5,
        "negative": 5,
    }
    assert {
        mention.product_id for row in rows for mention in row.mentions
    } <= catalog_ids
