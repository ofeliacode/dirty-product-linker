"""Explainable feature-aware reranking over lexical and dense candidates."""

from dataclasses import dataclass

from dirty_product_linker.linking.lexical import LinkCandidate, LinkResult
from dirty_product_linker.normalization.text import normalize_text
from dirty_product_linker.schemas import Product, ProductCategory

BRAND_ALIASES = {
    "apple": ("apple", "эпл"),
    "asus": ("asus", "асус"),
    "bose": ("bose", "боуз"),
    "bosch": ("bosch", "бош"),
    "dell": ("dell", "делл"),
    "dyson": ("dyson", "дайсон"),
    "google": ("google", "гугл"),
    "lg": ("lg", "эл джи", "элджи"),
    "lenovo": ("lenovo", "леново"),
    "oneplus": ("oneplus", "one plus", "ванплас"),
    "roborock": ("roborock", "роборок"),
    "samsung": ("samsung", "самсунг", "самсунь"),
    "sennheiser": ("sennheiser", "сенхайзер"),
    "sony": ("sony", "сони"),
    "tcl": ("tcl", "тсл"),
}

CATEGORY_TERMS = {
    ProductCategory.SMARTPHONE: ("телефон", "смартфон", "android", "андроид"),
    ProductCategory.LAPTOP: ("ноутбук", "ноут", "лэптоп"),
    ProductCategory.HEADPHONES: (
        "наушники",
        "внутриканальные",
        "полноразмерные",
    ),
    ProductCategory.TELEVISION: ("телевизор", "телек", "tv"),
    ProductCategory.HOME_APPLIANCE: (
        "холодильник",
        "стиральная",
        "стиралка",
        "пылесос",
    ),
}

ATTRIBUTE_ALIASES = {
    "black": ("black", "черный", "черные", "черного"),
    "gray": ("gray", "серый", "серого"),
    "green": ("green", "зеленый", "зеленого"),
    "silver": ("silver", "серебристый", "серебристого"),
    "white": ("white", "белый", "белая", "белые", "белого"),
    "9": ("9", "девять"),
    "13.4": ("13.4", "тринадцать"),
    "14": ("14", "четырнадцать"),
    "55": ("55",),
    "128": ("128",),
    "256": ("256",),
    "512": ("512",),
}


@dataclass(frozen=True, slots=True)
class CandidateFeatures:
    """Normalized evidence used to score one catalog candidate."""

    lexical_score: float
    dense_score: float
    alias_evidence: float
    brand_evidence: float
    category_compatibility: float
    model_token_overlap: float
    attribute_agreement: float
    combined_score: float


@dataclass(frozen=True, slots=True)
class FeatureAwareResult(LinkResult):
    """Reranked decision with inspectable evidence for every candidate."""

    decision_source: str
    margin: float
    features_by_product: dict[str, CandidateFeatures]


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    padded = f" {text.casefold()} "
    return any(f" {phrase.casefold()} " in padded for phrase in phrases)


def _brand_evidence(query: str, product: Product) -> float:
    canonical = normalize_text(product.brand)
    aliases = BRAND_ALIASES.get(canonical, (canonical,))
    return float(_contains_phrase(query, aliases))


def _alias_evidence(query: str, product: Product) -> float:
    aliases = tuple(
        normalized
        for alias in product.aliases
        if len((normalized := normalize_text(alias)).replace(" ", "")) >= 3
    )
    return float(_contains_phrase(normalize_text(query), aliases))


def _category_compatibility(query: str, category: ProductCategory) -> float:
    return float(_contains_phrase(query, CATEGORY_TERMS[category]))


def _model_token_overlap(query: str, product: Product) -> float:
    query_tokens = set(normalize_text(query).split())
    model_text = f"{product.family or ''} {product.model}"
    model_tokens = {
        token
        for token in normalize_text(model_text).split()
        if token not in {normalize_text(product.brand)} and len(token) >= 2
    }
    if not model_tokens:
        return 0.0
    return len(query_tokens & model_tokens) / len(model_tokens)


def _attribute_agreement(query: str, product: Product) -> float:
    if not product.attributes:
        return 0.0
    matched = 0
    for value in product.attributes.values():
        normalized = normalize_text(str(value))
        aliases = ATTRIBUTE_ALIASES.get(normalized, (normalized,))
        matched += int(_contains_phrase(query, aliases))
    return matched / len(product.attributes)


class FeatureAwareReranker:
    """Rerank a union candidate pool and abstain without identity evidence."""

    def __init__(
        self,
        products: list[Product],
        *,
        min_score: float = 0.4,
        min_margin: float = 0.08,
    ) -> None:
        if not products:
            raise ValueError("products cannot be empty")
        if not 0 <= min_score <= 1:
            raise ValueError("min_score must be between zero and one")
        if not 0 <= min_margin <= 1:
            raise ValueError("min_margin must be between zero and one")
        self._products = {product.product_id: product for product in products}
        self._min_score = min_score
        self._min_margin = min_margin

    def rerank(
        self,
        text: str,
        *,
        lexical: LinkResult,
        dense: LinkResult,
        top_k: int = 5,
    ) -> FeatureAwareResult:
        """Score the union of both top-k lists with explicit catalog evidence."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        lexical_scores = {
            candidate.product_id: candidate.score for candidate in lexical.candidates
        }
        dense_scores = {
            candidate.product_id: candidate.score for candidate in dense.candidates
        }
        candidate_ids = set(lexical_scores) | set(dense_scores)
        unknown_ids = candidate_ids - set(self._products)
        if unknown_ids:
            raise ValueError(f"candidate products are missing from catalog: {unknown_ids}")

        features_by_product: dict[str, CandidateFeatures] = {}
        for product_id in sorted(candidate_ids):
            product = self._products[product_id]
            lexical_score = max(0.0, lexical_scores.get(product_id, 0.0))
            dense_score = max(0.0, dense_scores.get(product_id, 0.0))
            alias = _alias_evidence(text, product)
            brand = _brand_evidence(text, product)
            category = _category_compatibility(text, product.category)
            model = _model_token_overlap(text, product)
            attributes = _attribute_agreement(text, product)
            combined = min(
                1.0,
                0.30 * brand
                + 0.15 * category
                + 0.15 * model
                + 0.10 * attributes
                + 0.20 * dense_score
                + 0.10 * lexical_score
                + 0.30 * alias,
            )
            features_by_product[product_id] = CandidateFeatures(
                lexical_score=round(lexical_score, 6),
                dense_score=round(dense_score, 6),
                alias_evidence=alias,
                brand_evidence=brand,
                category_compatibility=category,
                model_token_overlap=round(model, 6),
                attribute_agreement=round(attributes, 6),
                combined_score=round(combined, 6),
            )

        candidates = tuple(
            LinkCandidate(
                product_id=product_id,
                score=features.combined_score,
                matched_surface="feature_reranker",
            )
            for product_id, features in sorted(
                features_by_product.items(),
                key=lambda item: (-item[1].combined_score, item[0]),
            )[:top_k]
        )
        best = candidates[0]
        second_score = candidates[1].score if len(candidates) > 1 else 0.0
        margin = best.score - second_score
        best_features = features_by_product[best.product_id]
        has_identity = (
            best_features.alias_evidence > 0
            or best_features.brand_evidence > 0
            or best_features.model_token_overlap >= 0.25
        )
        if not has_identity:
            source = "abstain_no_identity"
        elif best.score < self._min_score:
            source = "abstain_low_score"
        elif margin < self._min_margin:
            source = "abstain_low_margin"
        else:
            source = "feature_reranker"
        accepted = source == "feature_reranker"
        return FeatureAwareResult(
            status="linked" if accepted else "unknown",
            product_id=best.product_id if accepted else None,
            score=best.score,
            candidates=candidates,
            decision_source=source,
            margin=round(margin, 6),
            features_by_product=features_by_product,
        )
