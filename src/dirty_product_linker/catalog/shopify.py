"""Pure transformations from Shopify catalogue rows to project products."""

import hashlib
import json
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from dirty_product_linker.schemas import Product, ProductCategory

SOURCE_ID = "Shopify/product-catalogue"

_CATEGORY_MARKERS: tuple[tuple[str, ProductCategory], ...] = (
    ("mobile phones", ProductCategory.SMARTPHONE),
    ("laptops", ProductCategory.LAPTOP),
    ("headphones", ProductCategory.HEADPHONES),
    ("televisions", ProductCategory.TELEVISION),
    ("appliances", ProductCategory.HOME_APPLIANCE),
)


class ShopifyRecordRejected(ValueError):
    """A source row that cannot safely become a supported catalog product."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class ShopifyImportResult:
    """Converted products plus an auditable accounting of rejected rows."""

    read: int
    products: tuple[Product, ...]
    rejection_reasons: dict[str, int]

    @property
    def accepted(self) -> int:
        return len(self.products)

    @property
    def rejected(self) -> int:
        return self.read - self.accepted


def _required_string(record: Mapping[str, object], field: str, reason: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ShopifyRecordRejected(reason)
    return value.strip()


def _map_category(source_category: str) -> ProductCategory:
    normalized = source_category.casefold()
    for marker, category in _CATEGORY_MARKERS:
        if marker in normalized:
            return category
    raise ShopifyRecordRejected("unsupported_category")


def _slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug[:60] or "product"


def _source_product_id(*, title: str, brand: str, source_category: str) -> str:
    identity = json.dumps(
        {"brand": brand, "category": source_category, "title": title},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode()).hexdigest()[:12]
    return f"shopify-{_slug(brand)}-{_slug(title)}-{digest}"


def convert_shopify_record(record: Mapping[str, object]) -> Product:
    """Convert one supported Shopify row or raise a reasoned rejection."""

    title = _required_string(record, "product_title", "missing_title")
    brand = _required_string(record, "ground_truth_brand", "missing_brand")
    source_category = _required_string(
        record, "ground_truth_category", "missing_source_category"
    )
    category = _map_category(source_category)
    is_secondhand = record.get("ground_truth_is_secondhand", False)

    if not isinstance(is_secondhand, bool):
        raise ShopifyRecordRejected("invalid_secondhand_flag")

    return Product(
        product_id=_source_product_id(
            title=title,
            brand=brand,
            source_category=source_category,
        ),
        category=category,
        brand=brand,
        model=title,
        attributes={
            "source": SOURCE_ID,
            "source_category": source_category,
            "is_secondhand": is_secondhand,
        },
        aliases=[title],
    )


def import_shopify_records(records: Iterable[Mapping[str, object]]) -> ShopifyImportResult:
    """Convert rows while retaining counts for every rejected record."""

    products: list[Product] = []
    rejection_reasons: Counter[str] = Counter()
    read = 0

    for record in records:
        read += 1
        try:
            products.append(convert_shopify_record(record))
        except ShopifyRecordRejected as error:
            rejection_reasons[error.reason] += 1

    return ShopifyImportResult(
        read=read,
        products=tuple(products),
        rejection_reasons=dict(sorted(rejection_reasons.items())),
    )
