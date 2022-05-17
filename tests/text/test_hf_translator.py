import pytest

from medkit.core.text import Segment, Span, ModifiedSpan, span_utils
from medkit.text.hf_translator import HFTranslator, _Aligner
from medkit.text.ner import RegexpMatcher, RegexpMatcherRule


_TEXT_FR = "Je souffre d'insuffisance cardiaque depuis 10 ans."
_TEXT_EN = "I've been suffering from heart failure for 10 years."
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


def _get_raw_text_segment(text):
    return Segment(
        label="raw_text",
        spans=[Span(0, len(text))],
        text=text,
    )


@pytest.fixture(scope="module")
def translator_fr_to_en():
    return HFTranslator()


@pytest.fixture(scope="module")
def translator_en_to_fr():
    return HFTranslator(translation_model="Helsinki-NLP/opus-mt-en-fr")


def test_translator_fr_to_en(translator_fr_to_en):
    segment = _get_raw_text_segment(_TEXT_FR)
    translated_segment = translator_fr_to_en.run([segment])[0]
    assert translated_segment.text == _TEXT_EN


def test_translator_en_to_fr(translator_en_to_fr):
    segment = _get_raw_text_segment(_TEXT_EN)
    translated_segment = translator_en_to_fr.run([segment])[0]
    assert translated_segment.text == _TEXT_FR


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


def test_translator_with_matcher(translator_fr_to_en):
    """Make sure we are able to link an entity matched on translated text back to original text"""
    rule = RegexpMatcherRule(
        regexp="heart failure",
        label="heart failure",
        id="id_heart_failure",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])

    segment = _get_raw_text_segment(_TEXT_FR)
    translated_segment = translator_fr_to_en.run([segment])[0]

    entities = matcher.run([translated_segment])
    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "heart failure"
    assert entity.text == "heart failure"

    text_alignments = _get_text_alignments(_TEXT_FR, translated_segment)
    assert text_alignments == _TEXT_ALIGNMENTS

    spans = span_utils.normalize_spans(entity.spans)
    spans = span_utils.clean_up_gaps_in_normalized_spans(spans, _TEXT_FR)
    matched_original_text = " ".join(segment.text[s.start : s.end] for s in spans)
    assert matched_original_text == "insuffisance cardiaque"


def test_ranges_sorting():
    aligner = _Aligner(alignment_model="aneuraz/awesome-align-with-co")
    range_alignments = aligner.align(
        "CHIRURGICAL ANTICEDENTS: surgery",
        "ANTÉCÉDENT CHIRURGICAUX: chirurgie",
    )
    assert all(sorted(r) == r for r in range_alignments.values())
