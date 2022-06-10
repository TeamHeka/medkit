from medkit.core.text import ModifiedSpan, Span
from medkit.core.text import Segment
from medkit.text.preprocessing import Normalizer, NormalizerRule


def _get_segment_from_text(text):
    return Segment(
        label="raw_text",
        spans=[Span(0, len(text))],
        text=text,
    )


def test_run():
    text = "À l'aide d'une canule n ° 3,"
    segment = _get_segment_from_text(text)

    rules = [NormalizerRule(*rule) for rule in [(r"n\s*°", "number")]]
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
