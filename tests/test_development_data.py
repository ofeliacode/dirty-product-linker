import json
from pathlib import Path

from dirty_product_linker.schemas import AnnotatedQuery, Product

PROJECT_ROOT = Path(__file__).parents[1]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def test_retrieval_dev_set_is_synthetic_valid_and_catalog_bound() -> None:
    dev_rows = read_jsonl(
        PROJECT_ROOT / "data/development/retrieval_dev_v0_1.jsonl"
    )
    catalog_rows = read_jsonl(PROJECT_ROOT / "data/catalog/sample_catalog.jsonl")
    product_ids = {Product.model_validate(row).product_id for row in catalog_rows}
    queries = [AnnotatedQuery.model_validate(row) for row in dev_rows]

    assert len(queries) == 24
    assert len({query.query_id for query in queries}) == 24
    assert all(query.provenance == "synthetic" for query in queries)
    assert all(set(query.target_product_ids) <= product_ids for query in queries)
    assert sum(query.answerable for query in queries) == 18


def test_retrieval_dev_text_does_not_duplicate_frozen_benchmark_text() -> None:
    dev_queries = [
        AnnotatedQuery.model_validate(row)
        for row in read_jsonl(
            PROJECT_ROOT / "data/development/retrieval_dev_v0_1.jsonl"
        )
    ]
    frozen_rows = read_jsonl(
        PROJECT_ROOT / "data/benchmark/frozen/ru_dirty_v0_1.jsonl"
    )
    frozen_texts = {str(row["text"]).casefold().strip() for row in frozen_rows}

    assert not ({query.text.casefold().strip() for query in dev_queries} & frozen_texts)
