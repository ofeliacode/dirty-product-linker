"""Promote explicitly approved candidates into human-reviewed benchmark slices."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from dirty_product_linker.schemas import (
    AnnotatedQuery,
    DataProvenance,
    MultiProductQuery,
)


@dataclass(frozen=True, slots=True)
class ReviewPromotionResult:
    """Audit values recorded when candidates are accepted by a person."""

    example_count: int
    candidate_sha256: str
    reviewed_sha256: str
    slice_counts: dict[str, int]


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def promote_reviewed_candidates(
    *,
    slices: Mapping[str, Sequence[AnnotatedQuery]],
    reviewed_dir: Path,
    manifest_path: Path,
    reviewer: str,
    reviewed_at: str,
) -> ReviewPromotionResult:
    """Record a human attestation and copy approved rows with human provenance."""

    if not reviewer.strip():
        raise ValueError("reviewer cannot be empty")
    if not reviewed_at.strip():
        raise ValueError("reviewed_at cannot be empty")
    if not slices:
        raise ValueError("at least one candidate slice is required")

    candidate_lines: list[str] = []
    reviewed_lines: list[str] = []
    reviewed_by_slice: dict[str, bytes] = {}
    slice_counts: dict[str, int] = {}
    seen_query_ids: set[str] = set()

    for slice_name in sorted(slices):
        rows: list[str] = []
        queries = sorted(slices[slice_name], key=lambda item: item.query_id)
        slice_counts[slice_name] = len(queries)
        for query in queries:
            if query.provenance is not DataProvenance.SYNTHETIC:
                raise ValueError(
                    f"expected synthetic candidate, got {query.provenance.value}: "
                    f"{query.query_id}"
                )
            if query.query_id in seen_query_ids:
                raise ValueError(f"duplicate query_id: {query.query_id}")
            seen_query_ids.add(query.query_id)

            candidate_line = query.model_dump_json() + "\n"
            reviewed = query.model_copy(
                update={"provenance": DataProvenance.HUMAN}
            )
            reviewed_line = reviewed.model_dump_json() + "\n"
            candidate_lines.append(f"{slice_name}:{candidate_line}")
            reviewed_lines.append(f"{slice_name}:{reviewed_line}")
            rows.append(reviewed_line)
        reviewed_by_slice[slice_name] = "".join(rows).encode()

    candidate_sha256 = hashlib.sha256("".join(candidate_lines).encode()).hexdigest()
    reviewed_sha256 = hashlib.sha256("".join(reviewed_lines).encode()).hexdigest()
    result = ReviewPromotionResult(
        example_count=len(seen_query_ids),
        candidate_sha256=candidate_sha256,
        reviewed_sha256=reviewed_sha256,
        slice_counts=slice_counts,
    )

    for slice_name, content in reviewed_by_slice.items():
        _atomic_write(reviewed_dir / f"{slice_name}.jsonl", content)

    manifest = {
        "schema_version": "1.0",
        "reviewer": reviewer.strip(),
        "reviewed_at": reviewed_at.strip(),
        "example_count": result.example_count,
        "slice_counts": result.slice_counts,
        "candidate_sha256": result.candidate_sha256,
        "reviewed_sha256": result.reviewed_sha256,
        "attestation": "reviewer approved every row and its annotations",
    }
    _atomic_write(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(),
    )
    return result


def promote_reviewed_multi_product_candidates(
    *,
    queries: Sequence[MultiProductQuery],
    reviewed_path: Path,
    manifest_path: Path,
    reviewer: str,
    reviewed_at: str,
) -> ReviewPromotionResult:
    """Promote an explicitly approved multi-product candidate file."""

    if not reviewer.strip():
        raise ValueError("reviewer cannot be empty")
    if not reviewed_at.strip():
        raise ValueError("reviewed_at cannot be empty")
    if not queries:
        raise ValueError("queries cannot be empty")

    candidate_lines: list[str] = []
    reviewed_lines: list[str] = []
    slice_counts: dict[str, int] = {}
    seen_query_ids: set[str] = set()
    for query in sorted(queries, key=lambda item: item.query_id):
        if query.provenance is not DataProvenance.SYNTHETIC:
            raise ValueError(
                f"expected synthetic candidate, got {query.provenance.value}: "
                f"{query.query_id}"
            )
        if query.query_id in seen_query_ids:
            raise ValueError(f"duplicate query_id: {query.query_id}")
        seen_query_ids.add(query.query_id)
        slice_counts[query.slice_name] = slice_counts.get(query.slice_name, 0) + 1
        candidate_lines.append(query.model_dump_json() + "\n")
        reviewed_lines.append(
            query.model_copy(update={"provenance": DataProvenance.HUMAN}).model_dump_json()
            + "\n"
        )

    candidate_bytes = "".join(candidate_lines).encode()
    reviewed_bytes = "".join(reviewed_lines).encode()
    result = ReviewPromotionResult(
        example_count=len(queries),
        candidate_sha256=hashlib.sha256(candidate_bytes).hexdigest(),
        reviewed_sha256=hashlib.sha256(reviewed_bytes).hexdigest(),
        slice_counts=dict(sorted(slice_counts.items())),
    )
    _atomic_write(reviewed_path, reviewed_bytes)
    manifest = {
        "schema_version": "1.0",
        "benchmark_type": "multi_product_extraction",
        "reviewer": reviewer.strip(),
        "reviewed_at": reviewed_at.strip(),
        "example_count": result.example_count,
        "slice_counts": result.slice_counts,
        "candidate_sha256": result.candidate_sha256,
        "reviewed_sha256": result.reviewed_sha256,
        "attestation": "reviewer approved every query, product link, and character span",
    }
    _atomic_write(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(),
    )
    return result
