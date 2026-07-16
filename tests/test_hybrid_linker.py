from dirty_product_linker.linking.hybrid import HybridProductLinker
from dirty_product_linker.linking.lexical import LinkCandidate, LinkResult


class StubLinker:
    def __init__(self, result: LinkResult) -> None:
        self._result = result

    def link(self, text: str, *, top_k: int = 5) -> LinkResult:
        return self._result


def result(
    status: str,
    product_id: str,
    score: float,
    second_product_id: str,
    second_score: float,
) -> LinkResult:
    return LinkResult(
        status=status,
        product_id=product_id if status == "linked" else None,
        score=score,
        candidates=(
            LinkCandidate(product_id, score, product_id),
            LinkCandidate(second_product_id, second_score, second_product_id),
        ),
    )


def test_confident_lexical_decision_wins_over_conflicting_dense_result() -> None:
    lexical = result("linked", "iphone", 0.8, "samsung", 0.2)
    dense = result("linked", "samsung", 0.9, "iphone", 0.6)
    linker = HybridProductLinker(
        lexical=StubLinker(lexical),
        dense=StubLinker(dense),
    )

    decision = linker.link("query")

    assert decision.status == "linked"
    assert decision.product_id == "iphone"
    assert decision.decision_source == "lexical"


def test_dense_recovers_when_weak_lexical_candidate_agrees_with_clear_dense_top() -> None:
    lexical = result("unknown", "iphone", 0.2, "samsung", 0.1)
    dense = result("linked", "iphone", 0.75, "samsung", 0.5)
    linker = HybridProductLinker(
        lexical=StubLinker(lexical),
        dense=StubLinker(dense),
    )

    decision = linker.link("query")

    assert decision.status == "linked"
    assert decision.product_id == "iphone"
    assert decision.decision_source == "dense_fallback"


def test_dense_fallback_rejects_small_top_two_margin() -> None:
    lexical = result("unknown", "iphone", 0.2, "samsung", 0.1)
    dense = result("linked", "iphone", 0.75, "samsung", 0.7)
    linker = HybridProductLinker(
        lexical=StubLinker(lexical),
        dense=StubLinker(dense),
    )

    decision = linker.link("query")

    assert decision.status == "unknown"
    assert decision.product_id is None
    assert decision.decision_source == "abstain"


def test_dense_fallback_rejects_disagreement_with_weak_lexical_top() -> None:
    lexical = result("unknown", "samsung", 0.2, "iphone", 0.1)
    dense = result("linked", "iphone", 0.8, "samsung", 0.5)
    linker = HybridProductLinker(
        lexical=StubLinker(lexical),
        dense=StubLinker(dense),
    )

    decision = linker.link("query")

    assert decision.status == "unknown"
    assert decision.decision_source == "abstain"
