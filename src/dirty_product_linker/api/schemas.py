"""Public request and response contracts for the inference API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class ApiModel(BaseModel):
    """Strict base model so client mistakes fail loudly."""

    model_config = ConfigDict(extra="forbid")


class LinkRequest(ApiModel):
    """One noisy product mention submitted for resolution."""

    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
    ]


class ProductSummary(ApiModel):
    """Catalog fields useful to an API consumer."""

    product_id: str
    brand: str
    model: str
    category: str


class CandidateResponse(ProductSummary):
    """One ranked candidate with an inspectable matching surface."""

    score: float = Field(ge=0, le=1)
    matched_surface: str


class AnalysisResponse(ApiModel):
    """Versioned, explainable result returned by the demo runtime."""

    text: str
    status: Literal["linked", "unknown"]
    decision_source: str
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    processing_ms: float = Field(ge=0)
    model_version: str
    catalog_version: str
    product_id: str | None = None
    category: str | None = None
    selected_product: ProductSummary | None = None
    candidates: list[CandidateResponse] = Field(default_factory=list)
