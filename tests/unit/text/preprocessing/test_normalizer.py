from medkit.core.text import ModifiedSpan, Span
from medkit.core.text import Segment
from medkit.text.preprocessing import Normalizer, NormalizerRule, LIGATURE_RULES


def _get_segment_from_text(text):
    return Segment(
        label="raw_text",
        spans=[Span(0, len(text))],
        text=text,
    )


def test_user_rules():
    text = "À l'aide d'une canule n ° 3,"
    segment = _get_segment_from_text(text)

    rules = [NormalizerRule(r"n\s*°", "number")]
    norm_segments = Normalizer(output_label="NORM_TEXT", rules=rules).run([segment])

    assert len(norm_segments) == 1
    norm_segment = norm_segments[0]

    # Verify the text with ligatures
    assert norm_segment.text == "À l'aide d'une canule number 3,"
    assert norm_segment.spans == [
        Span(start=0, end=22),
        ModifiedSpan(length=6, replaced_spans=[Span(start=22, end=25)]),
        Span(start=25, end=28),
    ]


def test_ligature_rules():
    text_classic = "Il a un frère atteint de diabète."
    text_with_ligature = "Il a une sœur atteinte de diabète."
    segment_classic = _get_segment_from_text(text_classic)
    segment_with_ligature = _get_segment_from_text(text_with_ligature)
    norm_segments = Normalizer(
        output_label="NORMALIZED_TEXT", rules=LIGATURE_RULES
    ).run([segment_classic, segment_with_ligature])

    assert len(norm_segments) == 2
    norm_classic = norm_segments[0]
    norm_with_ligatures = norm_segments[1]

    # Verify that nothing is modified when classic text
    assert norm_classic.text == segment_classic.text
    assert norm_classic.spans == segment_classic.spans
    assert norm_classic.label == "NORMALIZED_TEXT"

    # Verify the text with ligatures
    assert norm_with_ligatures.text == "Il a une soeur atteinte de diabète."
    assert norm_with_ligatures.spans == [
        Span(start=0, end=10),
        ModifiedSpan(length=2, replaced_spans=[Span(start=10, end=11)]),
        Span(start=11, end=34),
    ]
