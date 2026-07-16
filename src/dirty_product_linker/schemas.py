"""Versioned data contracts for catalog records and annotated queries."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ProductId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
]
AttributeValue = str | int | float | bool


class StrictModel(BaseModel):
    """Base contract that rejects unknown fields and validates assignments."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ProductCategory(StrEnum):
    """Product categories supported by the first public benchmark."""

    SMARTPHONE = "smartphone"
    LAPTOP = "laptop"
    HEADPHONES = "headphones"
    TELEVISION = "television"
    HOME_APPLIANCE = "home_appliance"


class EntityType(StrEnum):
    """Entity labels extracted from a noisy product mention."""

    BRAND = "BRAND"
    FAMILY = "FAMILY"
    MODEL = "MODEL"
    STORAGE = "STORAGE"
    MEMORY = "MEMORY"
    COLOR = "COLOR"
    SIZE = "SIZE"
    CATEGORY = "CATEGORY"


class DataProvenance(StrEnum):
    """Origin of an example, retained to prevent synthetic test leakage."""

    HUMAN = "human"
    PUBLIC_DATASET = "public_dataset"
    SYNTHETIC = "synthetic"


class EsciLabel(StrEnum):
    """Amazon ESCI relevance between one query and one product."""

    EXACT = "E"
    SUBSTITUTE = "S"
    COMPLEMENT = "C"
    IRRELEVANT = "I"


class Product(StrictModel):
    """One canonical product or SKU in the searchable catalog."""

    schema_version: str = "1.0"
    product_id: ProductId
    category: ProductCategory
    brand: NonEmptyString
    family: NonEmptyString | None = None
    model: NonEmptyString
    attributes: dict[NonEmptyString, AttributeValue] = Field(default_factory=dict)
    aliases: list[NonEmptyString] = Field(default_factory=list)


class EntityAnnotation(StrictModel):
    """A labeled character span and its canonical normalized value."""

    type: EntityType
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: NonEmptyString
    normalized: NonEmptyString

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "EntityAnnotation":
        if self.end <= self.start:
            raise ValueError("entity end must be greater than start")
        return self


class AnnotatedQuery(StrictModel):
    """A noisy user query with gold spans and catalog links."""

    schema_version: str = "1.0"
    query_id: ProductId
    text: NonEmptyString
    language: NonEmptyString
    noise_types: list[NonEmptyString] = Field(default_factory=list)
    entities: list[EntityAnnotation] = Field(default_factory=list)
    target_product_ids: list[ProductId] = Field(default_factory=list)
    answerable: bool
    provenance: DataProvenance

    @model_validator(mode="after")
    def validate_query_consistency(self) -> "AnnotatedQuery":
        for entity in self.entities:
            if entity.end > len(self.text) or self.text[entity.start : entity.end] != entity.text:
                raise ValueError(
                    f"entity offsets do not match source text for {entity.text!r}"
                )

        if not self.answerable and self.target_product_ids:
            raise ValueError("unanswerable query cannot have target products")

        return self


class QueryProductJudgment(StrictModel):
    """One immutable relevance judgment imported from Amazon ESCI.

    This source contract deliberately stays separate from ``Product`` because
    ESCI does not provide the product taxonomy required by our catalog schema.
    """

    schema_version: str = "1.0"
    source_example_id: int = Field(ge=0)
    source_query_id: int = Field(ge=0)
    query: NonEmptyString
    source_product_id: NonEmptyString
    locale: Literal["us", "es", "jp"]
    label: EsciLabel
    source_split: Literal["train", "test"]
    source_revision: NonEmptyString
