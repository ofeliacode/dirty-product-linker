import json
from pathlib import Path

from dirty_product_linker.schemas import AnnotatedQuery, Product

PROJECT_ROOT = Path(__file__).parents[1]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def test_every_sample_catalog_row_matches_the_product_contract() -> None:
    rows = read_jsonl(PROJECT_ROOT / "data/catalog/sample_catalog.jsonl")

    products = [Product.model_validate(row) for row in rows]

    assert len(products) >= 5
    assert len({product.category for product in products}) >= 5
    assert len({product.product_id for product in products}) == len(products)


def test_every_annotated_example_matches_the_query_contract() -> None:
    rows = read_jsonl(PROJECT_ROOT / "data/examples/annotated_queries.jsonl")

    queries = [AnnotatedQuery.model_validate(row) for row in rows]

    assert len(queries) >= 5
    assert any(query.provenance == "human" for query in queries)
    assert any(not query.answerable for query in queries)


def test_every_target_product_exists_in_the_sample_catalog() -> None:
    product_rows = read_jsonl(PROJECT_ROOT / "data/catalog/sample_catalog.jsonl")
    query_rows = read_jsonl(PROJECT_ROOT / "data/examples/annotated_queries.jsonl")
    product_ids = {Product.model_validate(row).product_id for row in product_rows}

    for row in query_rows:
        query = AnnotatedQuery.model_validate(row)
        assert set(query.target_product_ids) <= product_ids
