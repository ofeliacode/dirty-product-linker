from dirty_product_linker.normalization.text import normalize_text


def test_normalization_handles_case_punctuation_and_noisy_brand_spelling() -> None:
    assert normalize_text("САМСУНЬ с24—ультра") == "samsung s24 ultra"


def test_normalization_unifies_cyrillic_product_terms() -> None:
    assert normalize_text("телек ЭЛДЖИ олед C3") == "television lg oled c3"


def test_normalization_separates_glued_storage_unit() -> None:
    assert normalize_text("256GB") == "256 gb"
