from medkit.core.text.span import (
    Span,
    remove,
    extract,
    _remove_in_spans,
    _extract_in_spans,
)


def test_remove():
    text = "Hello, my name is John Doe."
    spans = [Span(0, 27)]
    text, spans = remove(text, spans, [(0, 7), (22, 27)])
    assert text == "my name is John"
    assert spans == [Span(7, 22)]


def test_extract():
    text = "Hello, my name is John Doe."
    spans = [Span(0, 27)]
    text, spans = extract(text, spans, [(0, 7), (18, 22)])
    assert text == "Hello, John"
    assert spans == [Span(0, 7), Span(18, 22)]


def test_remove_in_spans():
    # only one span
    spans = [Span(10, 20)]
    # remove at begining
    assert _remove_in_spans(spans, [(0, 6)]) == [Span(16, 20)]
    # remove at end
    assert _remove_in_spans(spans, [(4, 10)]) == [Span(10, 14)]
    # remove inside
    assert _remove_in_spans(spans, [(4, 7)]) == [
        Span(10, 14),
        Span(17, 20),
    ]
    # remove fully
    assert _remove_in_spans(spans, [(0, 10)]) == []
    # remove several ranges
    assert _remove_in_spans(spans, [(3, 5), (7, 8)]) == [
        Span(10, 13),
        Span(15, 17),
        Span(18, 20),
    ]

    # several spans
    spans = [Span(10, 20), Span(30, 40), Span(50, 60)]
    # remove at end of 1st pan
    assert _remove_in_spans(spans, [(4, 10)]) == [
        Span(10, 14),
        Span(30, 40),
        Span(50, 60),
    ]
    # remove accross several spans (end of 1st span and begining of 2d span)
    assert _remove_in_spans(spans, [(4, 14)]) == [
        Span(10, 14),
        Span(34, 40),
        Span(50, 60),
    ]
    # remove accross several spans (remove end of 1st span, remove 2d span fully, remove begining of last span)
    assert _remove_in_spans(spans, [(4, 24)]) == [Span(10, 14), Span(54, 60)]
    # remove several ranges
    assert _remove_in_spans(spans, [(4, 14), (16, 24)]) == [
        Span(10, 14),
        Span(34, 36),
        Span(54, 60),
    ]


def test_extract_in_spans():
    # only one span
    spans = [Span(10, 20)]
    # extract begining
    assert _extract_in_spans(spans, [(0, 6)]) == [Span(10, 16)]
    # extract end
    assert _extract_in_spans(spans, [(4, 10)]) == [Span(14, 20)]
    # extract whole span
    assert _extract_in_spans(spans, [(0, 10)]) == [Span(10, 20)]
    # remove several ranges
    assert _extract_in_spans(spans, [(3, 5), (7, 8)]) == [
        Span(13, 15),
        Span(17, 18),
    ]

    # several spans
    spans = [Span(10, 20), Span(30, 40), Span(50, 60)]
    # extract end of 1st span
    assert _extract_in_spans(spans, [(4, 10)]) == [Span(14, 20)]
    # extract in several spans (end of 1st span and begining of 2d span)
    assert _extract_in_spans(spans, [(4, 14)]) == [
        Span(14, 20),
        Span(30, 34),
    ]
    # extract in several spans (end of 1st span, entire 2d span, begining of 3d span)
    assert _extract_in_spans(spans, [(4, 24)]) == [
        Span(14, 20),
        Span(30, 40),
        Span(50, 54),
    ]
    # extract several ranges
    assert _extract_in_spans(spans, [(4, 14), (16, 24)]) == [
        Span(14, 20),
        Span(30, 34),
        Span(36, 40),
        Span(50, 54),
    ]
