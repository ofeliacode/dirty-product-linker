from pathlib import Path

from dirty_product_linker.catalog.checkpoint import (
    load_import_checkpoint,
    run_checkpointed_import,
)
from dirty_product_linker.catalog.taxonomy import TaxonomyMap

PROJECT_ROOT = Path(__file__).parents[1]
TAXONOMY = TaxonomyMap.from_yaml(PROJECT_ROOT / "configs/data/taxonomy.yaml")


def supported_row(index: int) -> dict[str, object]:
    return {
        "product_title": f"Washing Machine {index}",
        "ground_truth_brand": "Example",
        "ground_truth_category": (
            "Home & Garden > Household Appliances > Laundry Appliances"
        ),
        "ground_truth_is_secondhand": False,
    }


def unsupported_row(index: int) -> dict[str, object]:
    return {
        "product_title": f"T-Shirt {index}",
        "ground_truth_brand": "Example",
        "ground_truth_category": "Apparel & Accessories > Clothing > Shirts",
        "ground_truth_is_secondhand": False,
    }


def test_checkpoint_persists_products_counts_and_source_identity(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.json"
    rows = [supported_row(1), unsupported_row(2), supported_row(3)]

    result = run_checkpointed_import(
        rows,
        taxonomy=TAXONOMY,
        checkpoint_path=checkpoint_path,
        checkpoint_every=2,
    )
    checkpoint = load_import_checkpoint(checkpoint_path)

    assert result.read == 3
    assert result.accepted == 2
    assert checkpoint.source_rows_processed == 3
    assert len(checkpoint.products) == 2
    assert checkpoint.rejection_reasons == {"unsupported_category": 1}
    assert checkpoint.dataset_id == "Shopify/product-catalogue"
    assert checkpoint.revision == "d5c517c509f5aca99053897ef1de797d6d7e5aa5"


def test_resumed_import_matches_one_uninterrupted_import(tmp_path: Path) -> None:
    rows = [
        supported_row(1),
        unsupported_row(2),
        supported_row(3),
        supported_row(4),
        unsupported_row(5),
    ]
    resumed_path = tmp_path / "resumed.json"

    run_checkpointed_import(
        rows[:3],
        taxonomy=TAXONOMY,
        checkpoint_path=resumed_path,
        checkpoint_every=2,
    )
    initial = load_import_checkpoint(resumed_path)
    resumed = run_checkpointed_import(
        rows[3:],
        taxonomy=TAXONOMY,
        checkpoint_path=resumed_path,
        checkpoint_every=2,
        initial=initial,
    )
    uninterrupted = run_checkpointed_import(
        rows,
        taxonomy=TAXONOMY,
        checkpoint_path=tmp_path / "uninterrupted.json",
        checkpoint_every=2,
    )

    assert resumed == uninterrupted
