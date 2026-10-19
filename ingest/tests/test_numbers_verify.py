from ingest.numbers import numbers_in, quote_supports
from ingest.verify import quote_in_document, verify_figure


def test_numbers_in_common_formats():
    assert numbers_in("at least 1,760 people") == [1760]
    assert numbers_in("12.7K metric tonnes") == [12700]
    assert numbers_in("1.4 million people") == [1_400_000]
    assert numbers_in("105,000 t") == [105000]


def test_quote_supports_allows_report_rounding():
    assert quote_supports(12700, "In June 2025, 12.7K metric tonnes")
    assert quote_supports(1760, "at least 1,760 Palestinians")
    assert not quote_supports(1761, "at least 1,760 Palestinians")


def test_quote_must_appear_word_for_word():
    doc = "We have recorded that at least 1,760 Palestinians have been killed while seeking aid."
    assert quote_in_document("at least 1,760 Palestinians have been killed while seeking aid", doc)
    assert not quote_in_document("at least 1,760 Palestinians were killed while seeking aid", doc)


def test_invented_figure_is_rejected():
    doc = "At least 1,760 Palestinians have been killed while seeking aid."
    problems = verify_figure(1960, "At least 1,760 Palestinians have been killed while seeking aid.", doc)
    assert problems and "does not state the value" in problems[0]
