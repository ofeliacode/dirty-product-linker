import json
from pathlib import Path

from dirty_product_linker.schemas import AnnotatedQuery, Product

PROJECT_ROOT = Path(__file__).parents[1]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def test_semantic_dev_is_valid_synthetic_and_bound_to_catalog_v0_2() -> None:
    queries = [
        AnnotatedQuery.model_validate(row)
        for row in read_jsonl(PROJECT_ROOT / "data/development/semantic_dev_v0_1.jsonl")
    ]
    products = [
        Product.model_validate(row)
        for row in read_jsonl(PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl")
    ]
    product_ids = {product.product_id for product in products}

    assert len(queries) == 25
    assert len({query.query_id for query in queries}) == 25
    assert sum(query.answerable for query in queries) == 20
    assert all(query.provenance == "synthetic" for query in queries)
    assert all(set(query.target_product_ids) <= product_ids for query in queries)


def test_semantic_dev_has_no_exact_text_overlap_with_previous_datasets() -> None:
    semantic_texts = {
        str(row["text"]).casefold().strip()
        for row in read_jsonl(PROJECT_ROOT / "data/development/semantic_dev_v0_1.jsonl")
    }
    previous_paths = [
        PROJECT_ROOT / "data/development/retrieval_dev_v0_1.jsonl",
        PROJECT_ROOT / "data/benchmark/frozen/ru_dirty_v0_1.jsonl",
    ]
    previous_texts = {
        str(row["text"]).casefold().strip()
        for path in previous_paths
        for row in read_jsonl(path)
    }

    assert not semantic_texts & previous_texts
