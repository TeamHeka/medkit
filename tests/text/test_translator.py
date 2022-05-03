import pytest

from medkit.core.text import Segment, Span, ModifiedSpan, span_utils
from medkit.text.translator import Translator, _Aligner
from medkit.text.ner import RegexpMatcher, RegexpMatcherRule


_ORIGINAL_TEXT = "Je souffre d'insuffisance cardiaque depuis 10 ans."
_TRANSLATED_TEXT = "I've been suffering from heart failure for 10 years."
_TEXT_ALIGNMENTS = [
    ("I", "Je"),
    ("'ve been ", None),
    ("suffering", "souffre"),
    (" ", None),
    ("from", "d"),
    (" ", None),
    ("heart", "cardiaque"),
    (" ", None),
    ("failure", "insuffisance"),
    (" ", None),
    ("for", "depuis"),
    (" ", None),
    ("10", "10"),
    (" ", None),
    ("years", "ans"),
    (".", "."),
]


def _get_raw_text_segment(text=_ORIGINAL_TEXT):
    return Segment(label="raw_text", spans=[Span(0, len(text))], text=text,)


@pytest.fixture(scope="module")
def translator():
    return Translator()


def test_translator(translator):
    segment = _get_raw_text_segment(_ORIGINAL_TEXT)
    translated_segment = translator.run([segment])[0]
    assert translated_segment.text == _TRANSLATED_TEXT


def _get_text_alignments(original_text, translated_segment):
    """Return a list of tuple associated each word in the translated text
    to its corresponding word in the original text (if any).
    This is to visualize alignment in an easier way than with spans"""
    text_alignments = []
    start = 0
    for span in translated_segment.spans:
        end = start + span.length
        translated_sub_text = translated_segment.text[start:end]
        if isinstance(span, ModifiedSpan):
            if span.replaced_spans:
                original_sub_text = " ".join(
                    original_text[s.start : s.end] for s in span.replaced_spans
                )
            else:
                original_sub_text = None
        else:
            original_sub_text = original_text[span.start : span.end]
        text_alignments.append((translated_sub_text, original_sub_text))
        start = end
    return text_alignments


def test_translator_with_matcher(translator):
    """Make sure we are able to link an entity matched on translated text back to original text"""
    rule = RegexpMatcherRule(
        regexp="heart failure",
        label="heart failure",
        id="id_heart_failure",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])

    segment = _get_raw_text_segment(_ORIGINAL_TEXT)
    translated_segment = translator.run([segment])[0]

    entities = matcher.run([translated_segment])
    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "heart failure"
    assert entity.text == "heart failure"

    text_alignments = _get_text_alignments(_ORIGINAL_TEXT, translated_segment)
    assert text_alignments == _TEXT_ALIGNMENTS

    spans = span_utils.normalize_spans(entity.spans)
    spans = span_utils.clean_up_gaps_in_normalized_spans(spans, _ORIGINAL_TEXT)
    matched_original_text = " ".join(segment.text[s.start : s.end] for s in spans)
    assert matched_original_text == "insuffisance cardiaque"


def test_ranges_sorting():
    aligner = _Aligner(alignment_model="aneuraz/awesome-align-with-co")
    range_alignments = aligner.align(
        "CHIRURGICAL ANTICEDENTS: surgery", "ANTÉCÉDENT CHIRURGICAUX: chirurgie",
    )
    assert all(sorted(r) == r for r in range_alignments.values())
