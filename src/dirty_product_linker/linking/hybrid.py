"""Conservative lexical-first policy with guarded dense fallback."""

from dataclasses import dataclass
from typing import Protocol

from dirty_product_linker.linking.lexical import LinkResult


class ProductLinker(Protocol):
    """Shared interface implemented by lexical and embedding linkers."""

    def link(self, text: str, *, top_k: int = 5) -> LinkResult:
        """Return one decision and ranked candidates."""
        ...


@dataclass(frozen=True, slots=True)
class HybridLinkResult(LinkResult):
    """Link decision plus the policy path and component evidence."""

    decision_source: str
    lexical_score: float
    dense_score: float | None
    dense_margin: float | None


class HybridProductLinker:
    """Prefer precise lexical evidence and invoke dense retrieval on abstention."""

    def __init__(
        self,
        *,
        lexical: ProductLinker,
        dense: ProductLinker,
        dense_min_score: float = 0.65,
        dense_min_margin: float = 0.12,
        lexical_support_score: float = 0.15,
    ) -> None:
        if not -1 <= dense_min_score <= 1:
            raise ValueError("dense_min_score must be between minus one and one")
        if not 0 <= dense_min_margin <= 2:
            raise ValueError("dense_min_margin must be between zero and two")
        if not 0 <= lexical_support_score <= 1:
            raise ValueError("lexical_support_score must be between zero and one")
        self._lexical = lexical
        self._dense = dense
        self._dense_min_score = dense_min_score
        self._dense_min_margin = dense_min_margin
        self._lexical_support_score = lexical_support_score

    def link(self, text: str, *, top_k: int = 5) -> HybridLinkResult:
        """Return early on lexical confidence, otherwise evaluate guarded dense evidence."""

        lexical = self._lexical.link(text, top_k=top_k)
        if lexical.status == "linked":
            return HybridLinkResult(
                status="linked",
                product_id=lexical.product_id,
                score=lexical.score,
                candidates=lexical.candidates,
                decision_source="lexical",
                lexical_score=lexical.score,
                dense_score=None,
                dense_margin=None,
            )

        dense = self._dense.link(text, top_k=max(top_k, 2))
        dense_margin = (
            dense.candidates[0].score - dense.candidates[1].score
            if len(dense.candidates) >= 2
            else 0.0
        )
        lexical_top = lexical.candidates[0]
        dense_top = dense.candidates[0]
        use_dense = (
            dense_top.score >= self._dense_min_score
            and dense_margin >= self._dense_min_margin
            and lexical_top.score >= self._lexical_support_score
            and lexical_top.product_id == dense_top.product_id
        )
        if use_dense:
            return HybridLinkResult(
                status="linked",
                product_id=dense_top.product_id,
                score=dense_top.score,
                candidates=dense.candidates[:top_k],
                decision_source="dense_fallback",
                lexical_score=lexical.score,
                dense_score=dense_top.score,
                dense_margin=round(dense_margin, 6),
            )
        return HybridLinkResult(
            status="unknown",
            product_id=None,
            score=lexical.score,
            candidates=lexical.candidates,
            decision_source="abstain",
            lexical_score=lexical.score,
            dense_score=dense_top.score,
            dense_margin=round(dense_margin, 6),
        )
