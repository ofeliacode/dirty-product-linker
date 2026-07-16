from dirty_product_linker.normalization.text import normalize_text


def test_normalization_handles_case_punctuation_and_noisy_brand_spelling() -> None:
    assert normalize_text("САМСУНЬ с24—ультра") == "samsung s24 ultra"


def test_normalization_unifies_cyrillic_product_terms() -> None:
    assert normalize_text("телек ЭЛДЖИ олед C3") == "television lg oled c3"


def test_normalization_separates_glued_storage_unit() -> None:
    assert normalize_text("256GB") == "256 gb"


def test_normalization_transliterates_product_terms_inside_glued_text() -> None:
    assert normalize_text("айфон15промакс") == "iphone15promax"
    assert normalize_text("самсунгс24у") == "samsungs24u"


def test_normalization_joins_phonetic_multi_token_brand() -> None:
    assert normalize_text("эл джи C3") == "lg c3"
