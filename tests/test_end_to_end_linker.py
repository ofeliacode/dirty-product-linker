from dirty_product_linker.linking.lexical import LinkCandidate, LinkResult
from dirty_product_linker.linking.pipeline import EndToEndProductLinker
from dirty_product_linker.linking.reranker import FeatureAwareResult


class RecordingRetriever:
    def __init__(self, result: LinkResult) -> None:
        self.result = result
        self.calls: list[tuple[str, int]] = []

    def link(self, text: str, *, top_k: int = 5) -> LinkResult:
        self.calls.append((text, top_k))
        return self.result


class RecordingReranker:
    def __init__(self, result: FeatureAwareResult) -> None:
        self.result = result
        self.calls: list[tuple[str, LinkResult, LinkResult, int]] = []

    def rerank(
        self,
        text: str,
        *,
        lexical: LinkResult,
        dense: LinkResult,
        top_k: int = 5,
    ) -> FeatureAwareResult:
        self.calls.append((text, lexical, dense, top_k))
        return self.result


def raw_result(product_id: str, score: float) -> LinkResult:
    candidate = LinkCandidate(product_id, score, product_id)
    return LinkResult("linked", product_id, score, (candidate,))


def final_result(product_id: str) -> FeatureAwareResult:
    candidate = LinkCandidate(product_id, 0.87, "feature_reranker")
    return FeatureAwareResult(
        status="linked",
        product_id=product_id,
        score=0.87,
        candidates=(candidate,),
        decision_source="feature_reranker",
        margin=0.24,
        features_by_product={},
    )


def test_pipeline_runs_both_retrievers_before_feature_reranking() -> None:
    lexical_result = raw_result("samsung-phone", 0.74)
    dense_result = raw_result("samsung-phone", 0.81)
    lexical = RecordingRetriever(lexical_result)
    dense = RecordingRetriever(dense_result)
    reranker = RecordingReranker(final_result("samsung-phone"))
    pipeline = EndToEndProductLinker(
        lexical=lexical,
        dense=dense,
        reranker=reranker,
        candidate_top_k=7,
    )

    result = pipeline.link("ищу самсунь с24 ультра серый", top_k=3)

    assert result.product_id == "samsung-phone"
    assert lexical.calls == [("ищу самсунь с24 ультра серый", 7)]
    assert dense.calls == [("ищу самсунь с24 ультра серый", 7)]
    assert reranker.calls == [
        ("ищу самсунь с24 ультра серый", lexical_result, dense_result, 3)
    ]


def test_pipeline_preserves_reranker_abstention() -> None:
    raw = raw_result("samsung-phone", 0.55)
    abstention = FeatureAwareResult(
        status="unknown",
        product_id=None,
        score=0.38,
        candidates=raw.candidates,
        decision_source="abstain_low_score",
        margin=0.03,
        features_by_product={},
    )
    pipeline = EndToEndProductLinker(
        lexical=RecordingRetriever(raw),
        dense=RecordingRetriever(raw),
        reranker=RecordingReranker(abstention),
    )

    result = pipeline.link("просто хороший телефон")

    assert result.status == "unknown"
    assert result.product_id is None
    assert result.decision_source == "abstain_low_score"
