"""Freeze manually reviewed benchmark slices with integrity metadata."""

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from dirty_product_linker.schemas import AnnotatedQuery, DataProvenance, Product


@dataclass(frozen=True, slots=True)
class BenchmarkFreezeResult:
    """Integrity information for one frozen benchmark release."""

    example_count: int
    sha256: str
    catalog_product_ids_sha256: str
    slice_counts: dict[str, int]


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def _catalog_ids_checksum(product_ids: set[str]) -> str:
    content = "".join(f"{product_id}\n" for product_id in sorted(product_ids)).encode()
    return hashlib.sha256(content).hexdigest()


def freeze_benchmark(
    *,
    slices: Mapping[str, Sequence[AnnotatedQuery]],
    catalog: Iterable[Product],
    output_path: Path,
    manifest_path: Path,
    benchmark_version: str,
) -> BenchmarkFreezeResult:
    """Validate reviewed slices and write a byte-stable benchmark release."""

    if not benchmark_version.strip():
        raise ValueError("benchmark_version cannot be empty")
    if not slices:
        raise ValueError("at least one benchmark slice is required")

    catalog_product_ids = {product.product_id for product in catalog}
    if not catalog_product_ids:
        raise ValueError("catalog cannot be empty")

    seen_query_ids: set[str] = set()
    serialized_rows: list[str] = []
    slice_counts: dict[str, int] = {}

    for slice_name in sorted(slices):
        if not slice_name.strip():
            raise ValueError("slice name cannot be empty")
        slice_queries = sorted(slices[slice_name], key=lambda item: item.query_id)
        slice_counts[slice_name] = len(slice_queries)

        for query in slice_queries:
            if query.provenance is not DataProvenance.HUMAN:
                raise ValueError(
                    f"query {query.query_id} is not human-reviewed; "
                    "synthetic candidates cannot enter the frozen benchmark"
                )
            if query.query_id in seen_query_ids:
                raise ValueError(f"duplicate query_id: {query.query_id}")
            seen_query_ids.add(query.query_id)

            unknown_targets = set(query.target_product_ids) - catalog_product_ids
            if unknown_targets:
                raise ValueError(
                    f"query {query.query_id} has unknown target product: "
                    f"{sorted(unknown_targets)}"
                )

            row = {"slice": slice_name, **query.model_dump(mode="json")}
            serialized_rows.append(
                json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
                + "\n"
            )

    benchmark_content = "".join(serialized_rows).encode()
    benchmark_sha256 = hashlib.sha256(benchmark_content).hexdigest()
    catalog_sha256 = _catalog_ids_checksum(catalog_product_ids)
    result = BenchmarkFreezeResult(
        example_count=len(serialized_rows),
        sha256=benchmark_sha256,
        catalog_product_ids_sha256=catalog_sha256,
        slice_counts=slice_counts,
    )
    manifest = {
        "schema_version": "1.0",
        "benchmark_version": benchmark_version,
        "example_count": result.example_count,
        "slice_counts": result.slice_counts,
        "sha256": result.sha256,
        "catalog_product_ids_sha256": result.catalog_product_ids_sha256,
        "provenance_requirement": "human",
    }

    _atomic_write(output_path, benchmark_content)
    _atomic_write(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(),
    )
    return result
