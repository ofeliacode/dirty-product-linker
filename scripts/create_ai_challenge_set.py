"""Create the AI-authored 100-query product-linking challenge set."""

from __future__ import annotations

from pathlib import Path

from dirty_product_linker.schemas import MultiProductQuery

OUTPUT_PATH = Path("data/benchmark/candidates/ai_challenge_v0_1.jsonl")

# Each mention is (surface text, canonical product_id). Offsets are derived below.
SLICES: dict[str, list[tuple[str, list[tuple[str, str]], list[str]]]] = {
    "ordinary_single": [
        (
            "хочу купить айфон 15 про макс на 256 гб",
            [("айфон 15 про макс", "apple-iphone-15-pro-max-256-black")],
            [],
        ),
        (
            "покажите Samsung Galaxy S24 Ultra серого цвета",
            [("Samsung Galaxy S24 Ultra", "samsung-galaxy-s24-ultra-256-gray")],
            [],
        ),
        (
            "нужен Google Pixel 8 Pro на 128 гигабайт",
            [("Google Pixel 8 Pro", "google-pixel-8-pro-128-black")],
            [],
        ),
        ("ищу зеленый OnePlus 12 с памятью 256", [("OnePlus 12", "oneplus-12-256-green")], []),
        (
            "можно заказать MacBook Pro 14 M3",
            [("MacBook Pro 14 M3", "apple-macbook-pro-14-m3-512")],
            [],
        ),
        ("мне нужен Dell XPS 13 9340 для работы", [("Dell XPS 13 9340", "dell-xps-13-9340")], []),
        (
            "есть в наличии ThinkPad X1 Carbon Gen 12",
            [("ThinkPad X1 Carbon Gen 12", "lenovo-thinkpad-x1-carbon-gen-12")],
            [],
        ),
        (
            "покажите ноутбук ASUS ROG Zephyrus G14 2024",
            [("ASUS ROG Zephyrus G14 2024", "asus-rog-zephyrus-g14-2024")],
            [],
        ),
        ("хочу черные Sony WH-1000XM5", [("Sony WH-1000XM5", "sony-wh-1000xm5-black")], []),
        (
            "нужны белые Apple AirPods Pro 2",
            [("Apple AirPods Pro 2", "apple-airpods-pro-2-white")],
            [],
        ),
        (
            "интересуют Bose QuietComfort Ultra",
            [("Bose QuietComfort Ultra", "bose-quietcomfort-ultra-black")],
            [],
        ),
        (
            "закажите Sennheiser Momentum 4 Wireless",
            [("Sennheiser Momentum 4 Wireless", "sennheiser-momentum-4-black")],
            [],
        ),
        ("ищу телевизор LG OLED C3 55 дюймов", [("LG OLED C3", "lg-oled-c3-55")], []),
        ("покажите Samsung QN90D на 55 дюймов", [("Samsung QN90D", "samsung-qn90d-55")], []),
        ("нужен Sony BRAVIA 8 OLED 55", [("Sony BRAVIA 8 OLED", "sony-bravia-8-oled-55")], []),
        ("есть ли TCL C855 диагональю 55", [("TCL C855", "tcl-c855-55")], []),
        (
            "нужен серебристый холодильник Bosch KGN39VL25R",
            [("Bosch KGN39VL25R", "bosch-kgn39vl25r-silver")],
            [],
        ),
        (
            "ищу стиральную машину Samsung WW90T554DAW",
            [("Samsung WW90T554DAW", "samsung-ww90t554daw-white")],
            [],
        ),
        (
            "хочу беспроводной пылесос Dyson V15 Detect",
            [("Dyson V15 Detect", "dyson-v15-detect")],
            [],
        ),
        (
            "покажите робот-пылесос Roborock S8 MaxV Ultra",
            [("Roborock S8 MaxV Ultra", "roborock-s8-maxv-ultra")],
            [],
        ),
    ],
    "slang_and_typos": [
        (
            "айофн 15 промакс есть?",
            [("айофн 15 промакс", "apple-iphone-15-pro-max-256-black")],
            ["typo", "transliteration"],
        ),
        (
            "самуснг с24 ультро серый нужен",
            [("самуснг с24 ультро", "samsung-galaxy-s24-ultra-256-gray")],
            ["typo", "transliteration"],
        ),
        (
            "пиксл 8прошку покажи",
            [("пиксл 8прошку", "google-pixel-8-pro-128-black")],
            ["typo", "colloquial"],
        ),
        (
            "ван плас двинашка зелененький",
            [("ван плас двинашка", "oneplus-12-256-green")],
            ["colloquial", "word_numbers"],
        ),
        (
            "мак про эмтри четырнаха нужен",
            [("мак про эмтри четырнаха", "apple-macbook-pro-14-m3-512")],
            ["slang", "word_numbers"],
        ),
        (
            "дел икспиэс тринашку глянуть",
            [("дел икспиэс тринашку", "dell-xps-13-9340")],
            ["transliteration", "colloquial"],
        ),
        (
            "ленововский карбон икс один новый",
            [("ленововский карбон икс один", "lenovo-thinkpad-x1-carbon-gen-12")],
            ["colloquial", "word_numbers"],
        ),
        (
            "рог зефирус джи14 игровой есть",
            [("рог зефирус джи14", "asus-rog-zephyrus-g14-2024")],
            ["transliteration", "slang"],
        ),
        (
            "соньки хм5 черненькие",
            [("соньки хм5", "sony-wh-1000xm5-black")],
            ["colloquial", "abbreviation"],
        ),
        (
            "эйрподсы прошки вторые",
            [("эйрподсы прошки вторые", "apple-airpods-pro-2-white")],
            ["colloquial", "word_numbers"],
        ),
        (
            "боус квайт комфорт ультро",
            [("боус квайт комфорт ультро", "bose-quietcomfort-ultra-black")],
            ["typo", "transliteration"],
        ),
        (
            "сенхи моментум четверки",
            [("сенхи моментум четверки", "sennheiser-momentum-4-black")],
            ["slang", "word_numbers"],
        ),
        (
            "лыжа олед цэ три пятдесят пять",
            [("лыжа олед цэ три", "lg-oled-c3-55")],
            ["slang", "word_numbers"],
        ),
        (
            "самс кьюэн девяносто дэ телек",
            [("самс кьюэн девяносто дэ", "samsung-qn90d-55")],
            ["slang", "transliteration"],
        ),
        (
            "соня бравиа восьмерка олед",
            [("соня бравиа восьмерка олед", "sony-bravia-8-oled-55")],
            ["colloquial", "word_numbers"],
        ),
        (
            "тисиэл си восимь пять пять",
            [("тисиэл си восимь пять пять", "tcl-c855-55")],
            ["typo", "word_numbers"],
        ),
        (
            "бошевский кэгээн тридцать девять",
            [("бошевский кэгээн тридцать девять", "bosch-kgn39vl25r-silver")],
            ["colloquial", "transliteration"],
        ),
        (
            "стиралка самс вэвэ девяносто",
            [("самс вэвэ девяносто", "samsung-ww90t554daw-white")],
            ["slang", "transliteration"],
        ),
        (
            "дайсн в пятнашка беспроводной",
            [("дайсн в пятнашка", "dyson-v15-detect")],
            ["typo", "colloquial"],
        ),
        (
            "робик эс восемь макс ви ультро",
            [("робик эс восемь макс ви ультро", "roborock-s8-maxv-ultra")],
            ["slang", "word_numbers"],
        ),
    ],
    "multi_product": [
        (
            "сравни айфон 15 про макс и Samsung S24 Ultra",
            [
                ("айфон 15 про макс", "apple-iphone-15-pro-max-256-black"),
                ("Samsung S24 Ultra", "samsung-galaxy-s24-ultra-256-gray"),
            ],
            [],
        ),
        (
            "покажи Pixel 8 Pro, OnePlus 12 и айфон 15 про макс",
            [
                ("Pixel 8 Pro", "google-pixel-8-pro-128-black"),
                ("OnePlus 12", "oneplus-12-256-green"),
                ("айфон 15 про макс", "apple-iphone-15-pro-max-256-black"),
            ],
            [],
        ),
        (
            "для офиса MacBook Pro 14 M3 и Dell XPS 13 9340",
            [
                ("MacBook Pro 14 M3", "apple-macbook-pro-14-m3-512"),
                ("Dell XPS 13 9340", "dell-xps-13-9340"),
            ],
            [],
        ),
        (
            "выбираю ThinkPad X1 Carbon Gen 12 или Zephyrus G14 2024",
            [
                ("ThinkPad X1 Carbon Gen 12", "lenovo-thinkpad-x1-carbon-gen-12"),
                ("Zephyrus G14 2024", "asus-rog-zephyrus-g14-2024"),
            ],
            [],
        ),
        (
            "к телефону добавь Sony WH-1000XM5 и AirPods Pro 2",
            [
                ("Sony WH-1000XM5", "sony-wh-1000xm5-black"),
                ("AirPods Pro 2", "apple-airpods-pro-2-white"),
            ],
            [],
        ),
        (
            "сравним Bose QuietComfort Ultra с Sennheiser Momentum 4 Wireless",
            [
                ("Bose QuietComfort Ultra", "bose-quietcomfort-ultra-black"),
                ("Sennheiser Momentum 4 Wireless", "sennheiser-momentum-4-black"),
            ],
            [],
        ),
        (
            "в зал LG OLED C3, а в спальню Samsung QN90D",
            [("LG OLED C3", "lg-oled-c3-55"), ("Samsung QN90D", "samsung-qn90d-55")],
            [],
        ),
        (
            "что лучше Sony BRAVIA 8 OLED или TCL C855",
            [("Sony BRAVIA 8 OLED", "sony-bravia-8-oled-55"), ("TCL C855", "tcl-c855-55")],
            [],
        ),
        (
            "закажи Bosch KGN39VL25R и Samsung WW90T554DAW",
            [
                ("Bosch KGN39VL25R", "bosch-kgn39vl25r-silver"),
                ("Samsung WW90T554DAW", "samsung-ww90t554daw-white"),
            ],
            [],
        ),
        (
            "для уборки Dyson V15 Detect плюс Roborock S8 MaxV Ultra",
            [
                ("Dyson V15 Detect", "dyson-v15-detect"),
                ("Roborock S8 MaxV Ultra", "roborock-s8-maxv-ultra"),
            ],
            [],
        ),
        (
            "нужны 15pm, sony xm5 и макбук про м3 14",
            [
                ("15pm", "apple-iphone-15-pro-max-256-black"),
                ("sony xm5", "sony-wh-1000xm5-black"),
                ("макбук про м3 14", "apple-macbook-pro-14-m3-512"),
            ],
            [],
        ),
        (
            "с24у жене, пиксель8про мне",
            [
                ("с24у", "samsung-galaxy-s24-ultra-256-gray"),
                ("пиксель8про", "google-pixel-8-pro-128-black"),
            ],
            [],
        ),
        (
            "положи ванплас 12 и эйрподсы про 2 в корзину",
            [
                ("ванплас 12", "oneplus-12-256-green"),
                ("эйрподсы про 2", "apple-airpods-pro-2-white"),
            ],
            [],
        ),
        (
            "между xps9340, карбоном 12 и g14 2024 что тише?",
            [
                ("xps9340", "dell-xps-13-9340"),
                ("карбоном 12", "lenovo-thinkpad-x1-carbon-gen-12"),
                ("g14 2024", "asus-rog-zephyrus-g14-2024"),
            ],
            [],
        ),
        (
            "боуз qc ultra или моментум четыре к айфону?",
            [
                ("боуз qc ultra", "bose-quietcomfort-ultra-black"),
                ("моментум четыре", "sennheiser-momentum-4-black"),
            ],
            [],
        ),
        (
            "покажи c3 55, qn90d 55 и бравию 8",
            [
                ("c3 55", "lg-oled-c3-55"),
                ("qn90d 55", "samsung-qn90d-55"),
                ("бравию 8", "sony-bravia-8-oled-55"),
            ],
            [],
        ),
        (
            "холодильник kgn39 рядом со стиралкой ww90",
            [("kgn39", "bosch-kgn39vl25r-silver"), ("ww90", "samsung-ww90t554daw-white")],
            [],
        ),
        (
            "сравни дайсон пятнадцать с робороком s8 maxv",
            [
                ("дайсон пятнадцать", "dyson-v15-detect"),
                ("робороком s8 maxv", "roborock-s8-maxv-ultra"),
            ],
            [],
        ),
        (
            "беру TCL C855 и Sony XM5, оформляйте",
            [("TCL C855", "tcl-c855-55"), ("Sony XM5", "sony-wh-1000xm5-black")],
            [],
        ),
        (
            "комплект: айфон пятнадцать про макс, макбук m3 и аирподсы вторые",
            [
                ("айфон пятнадцать про макс", "apple-iphone-15-pro-max-256-black"),
                ("макбук m3", "apple-macbook-pro-14-m3-512"),
                ("аирподсы вторые", "apple-airpods-pro-2-white"),
            ],
            [],
        ),
    ],
    "ambiguous": [
        ("а прошка на 256 еще осталась?", [], ["ambiguous_reference"]),
        ("покажите ультру в черном", [], ["ambiguous_model"]),
        ("нужна пятнашка, только не обычная", [], ["underspecified_model"]),
        ("есть последняя сонька?", [], ["ambiguous_brand"]),
        (
            "ищу карбон двенадцатого поколения",
            [("карбон двенадцатого поколения", "lenovo-thinkpad-x1-carbon-gen-12")],
            ["missing_brand"],
        ),
        ("дайте тот робот с максимальной базой", [], ["ambiguous_reference"]),
        ("хочу c3 для гостиной", [("c3", "lg-oled-c3-55")], ["short_model"]),
        (
            "мне восьмерку про на 128",
            [("восьмерку про", "google-pixel-8-pro-128-black")],
            ["missing_brand"],
        ),
        (
            "покажи модель на m3 с экраном 14",
            [("модель на m3 с экраном 14", "apple-macbook-pro-14-m3-512")],
            ["descriptive_reference"],
        ),
        (
            "нужен телевизор восемь олед",
            [("телевизор восемь олед", "sony-bravia-8-oled-55")],
            ["missing_brand"],
        ),
        ("какой-нибудь qn на 55", [("qn на 55", "samsung-qn90d-55")], ["partial_model"]),
        ("те самые наушники ультра", [], ["ambiguous_reference"]),
        (
            "хочу детект беспроводной",
            [("детект беспроводной", "dyson-v15-detect")],
            ["missing_brand"],
        ),
        ("нужна стиралка на девять килограмм", [], ["generic_attributes"]),
        (
            "дайте зеленый двенадцатый",
            [("зеленый двенадцатый", "oneplus-12-256-green")],
            ["descriptive_reference"],
        ),
    ],
    "negative": [
        ("подскажите время работы магазина", [], ["no_product"]),
        ("когда мой заказ передадут курьеру?", [], ["no_product"]),
        ("можно оплатить покупку частями?", [], ["no_product"]),
        ("хочу вернуть товар по гарантии", [], ["no_product"]),
        ("какие сегодня есть скидки", [], ["no_product"]),
        ("посоветуйте подарок папе", [], ["generic_intent"]),
        ("нужен хороший смартфон до ста тысяч", [], ["generic_category"]),
        ("ищу легкий ноутбук для поездок", [], ["generic_category"]),
        ("покажите беспроводные наушники", [], ["generic_category"]),
        ("телевизор какого размера подойдет с трех метров?", [], ["generic_category"]),
        ("нужна техника для новой кухни", [], ["generic_category"]),
        ("у вас есть доставка в выходные?", [], ["no_product"]),
        ("сравните цены с прошлой неделей", [], ["no_product"]),
        ("ничего не заказывайте, я еще думаю", [], ["negative_intent"]),
        ("спасибо, вопрос уже решен", [], ["no_product"]),
    ],
    "unseen_abbreviation": [
        (
            "нужен a15pm256blk",
            [("a15pm256blk", "apple-iphone-15-pro-max-256-black")],
            ["unseen_abbreviation"],
        ),
        (
            "покажи sg24u256",
            [("sg24u256", "samsung-galaxy-s24-ultra-256-gray")],
            ["unseen_abbreviation"],
        ),
        ("есть gp8p128?", [("gp8p128", "google-pixel-8-pro-128-black")], ["unseen_abbreviation"]),
        ("ищу op12g256", [("op12g256", "oneplus-12-256-green")], ["unseen_abbreviation"]),
        (
            "нужен mbp14m3/512",
            [("mbp14m3/512", "apple-macbook-pro-14-m3-512")],
            ["unseen_abbreviation"],
        ),
        ("покажи dx13-9340", [("dx13-9340", "dell-xps-13-9340")], ["unseen_abbreviation"]),
        (
            "есть tx1c-g12?",
            [("tx1c-g12", "lenovo-thinkpad-x1-carbon-gen-12")],
            ["unseen_abbreviation"],
        ),
        ("нужны wh1k-xm5", [("wh1k-xm5", "sony-wh-1000xm5-black")], ["unseen_abbreviation"]),
        (
            "покажи rqcu-black",
            [("rqcu-black", "bose-quietcomfort-ultra-black")],
            ["unseen_abbreviation"],
        ),
        ("ищу rr-s8mvu", [("rr-s8mvu", "roborock-s8-maxv-ultra")], ["unseen_abbreviation"]),
    ],
}

EXPECTED_COUNTS = {
    "ordinary_single": 20,
    "slang_and_typos": 20,
    "multi_product": 20,
    "ambiguous": 15,
    "negative": 15,
    "unseen_abbreviation": 10,
}


def build_rows() -> list[MultiProductQuery]:
    """Build validated rows and derive exact character offsets."""
    if {name: len(rows) for name, rows in SLICES.items()} != EXPECTED_COUNTS:
        raise ValueError("challenge-set slice counts do not match the specification")

    result: list[MultiProductQuery] = []
    sequence = 1
    for slice_name, examples in SLICES.items():
        for text, mention_specs, extra_noise in examples:
            mentions = []
            cursor = 0
            for surface, product_id in mention_specs:
                start = text.index(surface, cursor)
                end = start + len(surface)
                mentions.append(
                    {"start": start, "end": end, "text": surface, "product_id": product_id}
                )
                cursor = end
            noise_types = list(
                dict.fromkeys([*extra_noise, *(["multiple_products"] if len(mentions) > 1 else [])])
            )
            result.append(
                MultiProductQuery.model_validate(
                    {
                        "schema_version": "1.0",
                        "query_id": f"ai-challenge-{sequence:03d}",
                        "text": text,
                        "language": "ru-mixed"
                        if any(char.isascii() and char.isalpha() for char in text)
                        else "ru",
                        "slice_name": slice_name,
                        "noise_types": noise_types,
                        "mentions": mentions,
                        "provenance": "synthetic",
                    }
                )
            )
            sequence += 1
    return result


def main() -> None:
    rows = build_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{row.model_dump_json()}\n" for row in rows)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {len(rows)} AI-authored challenge queries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
