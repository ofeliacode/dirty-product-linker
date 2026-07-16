"""Explicit mapping from external taxonomy paths to project categories."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dirty_product_linker.schemas import ProductCategory

TaxonomyPath = tuple[str, ...]


class CategoryRules(BaseModel):
    """Allowed exact paths and parent subtrees for one project category."""

    model_config = ConfigDict(extra="forbid")

    exact_paths: list[str] = Field(default_factory=list)
    subtree_paths: list[str] = Field(default_factory=list)


class TaxonomyConfig(BaseModel):
    """Validated serialized taxonomy mapping."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    categories: dict[ProductCategory, CategoryRules]


def normalize_taxonomy_path(path: str) -> TaxonomyPath:
    """Normalize whitespace and case while preserving path segments."""

    segments = tuple(" ".join(segment.split()).casefold() for segment in path.split(">"))
    if not segments or any(not segment for segment in segments):
        raise ValueError(f"invalid taxonomy path: {path!r}")
    return segments


class TaxonomyMap:
    """Match source paths without broad substring heuristics."""

    def __init__(self, config: TaxonomyConfig) -> None:
        self.schema_version = config.schema_version
        self._exact: dict[TaxonomyPath, ProductCategory] = {}
        self._subtrees: list[tuple[TaxonomyPath, ProductCategory]] = []

        for category, rules in config.categories.items():
            for raw_path in rules.exact_paths:
                path = normalize_taxonomy_path(raw_path)
                self._register_exact(path, category)
            for raw_path in rules.subtree_paths:
                self._subtrees.append((normalize_taxonomy_path(raw_path), category))

    @classmethod
    def from_yaml(cls, path: Path) -> "TaxonomyMap":
        """Load and validate a versioned YAML mapping."""

        with path.open(encoding="utf-8") as source:
            config = TaxonomyConfig.model_validate(yaml.safe_load(source))
        return cls(config)

    def _register_exact(self, path: TaxonomyPath, category: ProductCategory) -> None:
        existing = self._exact.get(path)
        if existing is not None and existing is not category:
            raise ValueError(f"taxonomy path maps to multiple categories: {path!r}")
        self._exact[path] = category

    def match(self, source_path: str) -> ProductCategory | None:
        """Return one justified category or None for an unsupported path."""

        path = normalize_taxonomy_path(source_path)
        exact = self._exact.get(path)
        if exact is not None:
            return exact

        matches = {
            category
            for subtree, category in self._subtrees
            if len(path) >= len(subtree) and path[: len(subtree)] == subtree
        }
        if len(matches) > 1:
            raise ValueError(f"ambiguous taxonomy mapping for path: {source_path!r}")
        return next(iter(matches), None)
