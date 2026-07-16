"""Catalog-aware rule baseline for extracting explicit product mentions."""

import re
from dataclasses import dataclass

from dirty_product_linker.schemas import Product


@dataclass(frozen=True, slots=True)
class MentionSpan:
    """One non-overlapping character span in the original message."""

    text: str
    start: int
    end: int


def _surface_pattern(surface: str) -> re.Pattern[str]:
    tokens = re.findall(r"\w+", surface, flags=re.UNICODE)
    body = r"[\W_]*".join(re.escape(token) for token in tokens)
    return re.compile(rf"(?<!\w){body}(?!\w)", flags=re.IGNORECASE | re.UNICODE)


class CatalogMentionExtractor:
    """Find longest catalog names and aliases while preserving source offsets."""

    def __init__(self, products: list[Product]) -> None:
        surfaces = {
            surface.strip()
            for product in products
            for surface in (
                f"{product.brand} {product.model}",
                product.model,
                *product.aliases,
            )
            if len(re.sub(r"\W", "", surface, flags=re.UNICODE)) >= 3
        }
        self._patterns = tuple(
            _surface_pattern(surface)
            for surface in sorted(surfaces, key=lambda value: (-len(value), value.casefold()))
        )

    def extract(self, text: str) -> tuple[MentionSpan, ...]:
        """Return deterministic longest, non-overlapping matches in source order."""

        candidates = {
            (match.start(), match.end())
            for pattern in self._patterns
            for match in pattern.finditer(text)
        }
        ranked = sorted(candidates, key=lambda span: (-(span[1] - span[0]), span[0]))
        selected: list[tuple[int, int]] = []
        for start, end in ranked:
            overlaps = any(
                start < chosen_end and end > chosen_start
                for chosen_start, chosen_end in selected
            )
            if overlaps:
                continue
            selected.append((start, end))
        return tuple(
            MentionSpan(text=text[start:end], start=start, end=end)
            for start, end in sorted(selected)
        )
