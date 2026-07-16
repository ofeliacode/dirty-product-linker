"""End-to-end orchestration for retrieval, reranking, and abstention."""

from typing import Protocol

from dirty_product_linker.linking.lexical import LinkResult
from dirty_product_linker.linking.reranker import FeatureAwareResult


class Retriever(Protocol):
    """Candidate retriever shared by lexical and embedding implementations."""

    def link(self, text: str, *, top_k: int = 5) -> LinkResult:
        """Return ranked catalog candidates for one query."""


class Reranker(Protocol):
    """Combine retrieval evidence and make the final abstention decision."""

    def rerank(
        self,
        text: str,
        *,
        lexical: LinkResult,
        dense: LinkResult,
        top_k: int = 5,
    ) -> FeatureAwareResult:
        """Return a final explainable decision."""


class EndToEndProductLinker:
    """Run lexical retrieval, dense retrieval, feature reranking, and abstention."""

    def __init__(
        self,
        *,
        lexical: Retriever,
        dense: Retriever,
        reranker: Reranker,
        candidate_top_k: int = 5,
    ) -> None:
        if candidate_top_k < 1:
            raise ValueError("candidate_top_k must be at least 1")
        self._lexical = lexical
        self._dense = dense
        self._reranker = reranker
        self._candidate_top_k = candidate_top_k

    def link(self, text: str, *, top_k: int = 5) -> FeatureAwareResult:
        """Resolve one query while preserving the reranker's safe abstention."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        lexical = self._lexical.link(text, top_k=self._candidate_top_k)
        dense = self._dense.link(text, top_k=self._candidate_top_k)
        return self._reranker.rerank(
            text,
            lexical=lexical,
            dense=dense,
            top_k=top_k,
        )
