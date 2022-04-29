import pytest

from medkit.core.text import Segment, Span, ModifiedSpan, span_utils
from medkit.text.translator import Translator
from medkit.text.ner import RegexpMatcher, RegexpMatcherRule

_TEST_DATA = [
    # (
    #     "Ma soeur est diabétique.",
    #     "My sister is diabetic.",
    #     [("My", "Ma"), ("sister", "soeur"), ("is", "est"), ("diabetic", "diabétique"),],
    # ),
    (
        "Je souffre d'insuffisance cardiaque depuis 10 ans.",
        "I've been suffering from heart failure for 10 years.",
        [
            ("I", "Je"),
            ("suffering", "souffre"),
            ("from", "d"),
            ("heart", "cardiaque"),
            ("failure", "insuffisance"),
            ("for", "depuis"),
            ("10", "10"),
            ("years", "ans"),
        ],
    ),
]


def _get_word_alignments(original_text, translated_segment):
    word_alignments = []
    start = 0
    for span in translated_segment.spans:
        end = start + span.length
        translated_sub_text = translated_segment.text[start:end]
        if isinstance(span, ModifiedSpan):
            original_sub_text = " ".join(
                original_text[s.start : s.end] for s in span.replaced_spans
            )
        else:
            original_sub_text = original_text[span.start : span.end]
        if any(c.isalnum() for c in original_sub_text):
            word_alignments.append((translated_sub_text, original_sub_text))
        start = end
    return word_alignments


@pytest.fixture(scope="module")
def translator():
    return Translator()


@pytest.mark.parametrize(
    "original_text,expected_translated_text,expected_word_alignments", _TEST_DATA
)
def test_translator(
    translator, original_text, expected_translated_text, expected_word_alignments
):
    segment = Segment(
        label="raw_text",
        spans=[Span(0, len(original_text))],
        text=original_text,
    )

    translated_segment = translator.run([segment])[0]
    assert translated_segment.text == expected_translated_text

    word_alignments = _get_word_alignments(original_text, translated_segment)
    assert word_alignments == expected_word_alignments

    rule = RegexpMatcherRule(
        regexp="heart failure",
        label="heart failure",
        id="id_heart_failure",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entity = matcher.run([translated_segment])[0]
    spans = sorted(span_utils.normalize_spans(entity.spans))
    entity_original_words = [original_text[s.start : s.end] for s in spans]
    assert entity_original_words == ["insuffisance", "cardiaque"]
