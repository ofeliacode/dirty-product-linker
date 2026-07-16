import hashlib
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


def test_benchmark_candidates_are_valid_but_not_claimed_as_human_reviewed() -> None:
    product_rows = read_jsonl(PROJECT_ROOT / "data/catalog/sample_catalog.jsonl")
    product_ids = {Product.model_validate(row).product_id for row in product_rows}
    candidate_paths = sorted(
        (PROJECT_ROOT / "data/benchmark/candidates").glob("*.jsonl")
    )
    queries = [
        AnnotatedQuery.model_validate(row)
        for path in candidate_paths
        for row in read_jsonl(path)
    ]

    assert len(queries) == 20
    assert len({query.query_id for query in queries}) == len(queries)
    assert all(query.provenance == "synthetic" for query in queries)
    assert all(set(query.target_product_ids) <= product_ids for query in queries)


def test_frozen_benchmark_matches_manifest_and_contains_only_reviewed_rows() -> None:
    benchmark_path = (
        PROJECT_ROOT / "data/benchmark/frozen/ru_dirty_v0_1.jsonl"
    )
    manifest_path = (
        PROJECT_ROOT / "data/benchmark/frozen/ru_dirty_v0_1_manifest.json"
    )
    benchmark_bytes = benchmark_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in benchmark_bytes.decode().splitlines() if line]
    queries = [
        AnnotatedQuery.model_validate({key: value for key, value in row.items() if key != "slice"})
        for row in rows
    ]

    assert hashlib.sha256(benchmark_bytes).hexdigest() == manifest["sha256"]
    assert len(queries) == manifest["example_count"] == 20
    assert all(query.provenance == "human" for query in queries)
    assert {row["slice"] for row in rows} == {"ambiguous", "dirty", "negative"}


def test_review_attestation_matches_reviewed_slice_files() -> None:
    reviewed_dir = PROJECT_ROOT / "data/benchmark/reviewed"
    manifest = json.loads(
        (reviewed_dir / "review_manifest.json").read_text(encoding="utf-8")
    )
    queries = [
        AnnotatedQuery.model_validate(row)
        for path in sorted(reviewed_dir.glob("*.jsonl"))
        for row in read_jsonl(path)
    ]

    assert manifest["reviewer"] == "ofeliacode"
    assert manifest["reviewed_at"] == "2026-07-16"
    assert len(queries) == manifest["example_count"] == 20
    assert all(query.provenance == "human" for query in queries)
