"""Explainable dependency-free lexical product-linking baseline."""

from dataclasses import dataclass
from typing import Literal

from dirty_product_linker.normalization.text import normalize_text
from dirty_product_linker.schemas import Product

WEAK_CATEGORY_TOKENS = {
    "headphones",
    "home_appliance",
    "laptop",
    "smartphone",
    "television",
    "телевизор",
    "холодильник",
}


@dataclass(frozen=True, slots=True)
class LinkCandidate:
    """One ranked catalog candidate and its lexical score."""

    product_id: str
    score: float
    matched_surface: str


@dataclass(frozen=True, slots=True)
class LinkResult:
    """Baseline decision with explicit abstention and inspectable candidates."""

    status: Literal["linked", "unknown"]
    product_id: str | None
    score: float
    candidates: tuple[LinkCandidate, ...]


def _character_ngrams(value: str, size: int = 3) -> set[str]:
    compact = value.replace(" ", "")
    if len(compact) <= size:
        return {compact} if compact else set()
    return {compact[index : index + size] for index in range(len(compact) - size + 1)}


def _dice(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return 2 * len(left & right) / (len(left) + len(right))


def _token_f1(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    overlap = len(left_tokens & right_tokens)
    if not overlap:
        return 0.0
    precision = overlap / len(left_tokens)
    recall = overlap / len(right_tokens)
    return 2 * precision * recall / (precision + recall)


def _surface_score(query: str, surface: str) -> float:
    query = " ".join(token for token in query.split() if token not in WEAK_CATEGORY_TOKENS)
    surface = " ".join(
        token for token in surface.split() if token not in WEAK_CATEGORY_TOKENS
    )
    if not query or not surface:
        return 0.0
    if query == surface:
        return 1.0
    if len(surface) >= 3 and surface in query:
        return min(0.90, 0.78 + len(surface) / 100)
    compact_query = query.replace(" ", "")
    compact_surface = surface.replace(" ", "")
    if len(compact_surface) >= 3 and compact_surface in compact_query:
        return min(0.88, 0.76 + len(compact_surface) / 100)
    token_score = _token_f1(query, surface)
    character_score = _dice(_character_ngrams(query), _character_ngrams(surface))
    return 0.55 * token_score + 0.45 * character_score


def _product_surfaces(product: Product) -> tuple[str, ...]:
    raw_surfaces = [
        f"{product.brand} {product.model}",
        product.model,
        *product.aliases,
    ]
    if product.family:
        raw_surfaces.append(product.family)
        raw_surfaces.append(f"{product.brand} {product.family} {product.model}")
    return tuple(sorted({normalize_text(surface) for surface in raw_surfaces}))


class LexicalProductLinker:
    """Rank catalog products using aliases, tokens, and character trigrams."""

    def __init__(self, products: list[Product], *, min_score: float = 0.42) -> None:
        if not products:
            raise ValueError("products cannot be empty")
        if not 0 <= min_score <= 1:
            raise ValueError("min_score must be between zero and one")
        self._min_score = min_score
        self._index = tuple(
            (product.product_id, _product_surfaces(product))
            for product in sorted(products, key=lambda item: item.product_id)
        )

    def link(self, text: str, *, top_k: int = 5) -> LinkResult:
        """Return deterministic top-k candidates and abstain below the threshold."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query = normalize_text(text)
        ranked: list[LinkCandidate] = []
        for product_id, surfaces in self._index:
            score, surface = max(
                ((_surface_score(query, item), item) for item in surfaces),
                key=lambda item: (item[0], item[1]),
            )
            ranked.append(
                LinkCandidate(
                    product_id=product_id,
                    score=round(score, 6),
                    matched_surface=surface,
                )
            )
        candidates = tuple(
            sorted(ranked, key=lambda item: (-item.score, item.product_id))[:top_k]
        )
        best = candidates[0]
        if best.score < self._min_score:
            return LinkResult(
                status="unknown",
                product_id=None,
                score=best.score,
                candidates=candidates,
            )
        return LinkResult(
            status="linked",
            product_id=best.product_id,
            score=best.score,
            candidates=candidates,
        )
