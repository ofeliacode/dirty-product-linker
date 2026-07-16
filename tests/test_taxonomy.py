from pathlib import Path

import pytest

from dirty_product_linker.catalog.taxonomy import TaxonomyMap
from dirty_product_linker.schemas import ProductCategory

PROJECT_ROOT = Path(__file__).parents[1]
TAXONOMY_PATH = PROJECT_ROOT / "configs/data/taxonomy.yaml"


@pytest.fixture
def taxonomy() -> TaxonomyMap:
    return TaxonomyMap.from_yaml(TAXONOMY_PATH)


@pytest.mark.parametrize(
    ("source_path", "expected"),
    [
        (
            "Electronics > Communications > Telephony > Mobile Phones",
            ProductCategory.SMARTPHONE,
        ),
        ("Electronics > Computers > Laptops", ProductCategory.LAPTOP),
        (
            "Electronics > Audio > Audio Components > Headphones",
            ProductCategory.HEADPHONES,
        ),
        ("Electronics > Video > Televisions", ProductCategory.TELEVISION),
        (
            "Home & Garden > Household Appliances > Laundry Appliances > Dryers",
            ProductCategory.HOME_APPLIANCE,
        ),
    ],
)
def test_taxonomy_maps_supported_exact_paths_and_subtrees(
    taxonomy: TaxonomyMap,
    source_path: str,
    expected: ProductCategory,
) -> None:
    assert taxonomy.match(source_path) is expected


@pytest.mark.parametrize(
    "accessory_path",
    [
        "Electronics > Communications > Telephony > Mobile Phone Accessories > Cases",
        "Electronics > Computers > Laptop Accessories > Laptop Bags",
        "Electronics > Video > Television Accessories > TV Mounts",
    ],
)
def test_taxonomy_does_not_classify_accessories_as_devices(
    taxonomy: TaxonomyMap,
    accessory_path: str,
) -> None:
    assert taxonomy.match(accessory_path) is None


def test_taxonomy_normalizes_case_and_separator_whitespace(taxonomy: TaxonomyMap) -> None:
    source_path = " electronics>computers  > LAPTOPS "

    assert taxonomy.match(source_path) is ProductCategory.LAPTOP
