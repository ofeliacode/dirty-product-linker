"""Conservative normalization for noisy Russian product queries."""

import re
import unicodedata

TOKEN_REPLACEMENTS = {
    "айфон": "iphone",
    "самсунг": "samsung",
    "самсунь": "samsung",
    "сони": "sony",
    "элджи": "lg",
    "олед": "oled",
    "бош": "bosch",
    "телек": "television",
    "наушники": "headphones",
    "с24": "s24",
    "про": "pro",
    "макс": "max",
    "ультра": "ultra",
    "серый": "gray",
    "черный": "black",
    "черные": "black",
}


def normalize_text(text: str) -> str:
    """Normalize case, Unicode, punctuation, common spellings, and storage units."""

    normalized = unicodedata.normalize("NFKC", text).casefold().replace("ё", "е")
    normalized = re.sub(r"(?<=\d)(gb|гб)\b", r" \1", normalized)
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    tokens = [TOKEN_REPLACEMENTS.get(token, token) for token in normalized.split()]
    return " ".join(tokens)
