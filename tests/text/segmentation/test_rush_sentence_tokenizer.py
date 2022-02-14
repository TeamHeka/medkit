import pytest

from medkit.core.text import TextDocument
from medkit.core.text.annotation import TextBoundAnnotation
from medkit.core.text.span import Span, ModifiedSpan
from medkit.text.segmentation.rush_sentence_tokenizer import RushSentenceTokenizer


TEST_CONFIG = [
    (
        "Sentence testing the dot. Newlines\ndo not split. Test"
        " interrogation? Semicolon; and exclamation marks! do not split",
        RushSentenceTokenizer(input_label="RAW_TEXT"),
        [
            (
                "Sentence testing the dot.",
                [Span(start=0, end=25)],
            ),
            (
                "Newlines\ndo not split.",
                [Span(start=26, end=48)],
            ),
            (
                "Test interrogation?",
                [Span(start=49, end=68)],
            ),
            (
                "Semicolon; and exclamation marks! do not split",
                [Span(start=69, end=115)],
            ),
        ],
    ),
    (
        "Newlines\ncan be\nreplaced.",
        RushSentenceTokenizer(input_label="RAW_TEXT", keep_newlines=False),
        [
            (
                "Newlines can be replaced.",
                [
                    Span(start=0, end=8),
                    ModifiedSpan(length=1, replaced_spans=[Span(start=8, end=9)]),
                    Span(start=9, end=15),
                    ModifiedSpan(length=1, replaced_spans=[Span(start=15, end=16)]),
                    Span(start=16, end=25),
                ],
            ),
        ],
    ),
]


def _get_doc(text):
    doc = TextDocument()
    raw_text = TextBoundAnnotation(
        origin_id="", label="RAW_TEXT", spans=[Span(0, len(text))], text=text
    )
    doc.add_annotation(raw_text)
    return doc


@pytest.mark.parametrize(
    "text,sentence_tokenizer,expected_sentences",
    TEST_CONFIG,
    ids=["default", "keep_newlines"],
)
def test_default_rules(text, sentence_tokenizer, expected_sentences):
    assert sentence_tokenizer.input_label == "RAW_TEXT"

    doc = _get_doc(text)
    sentence_tokenizer.annotate_document(doc)
    sentences = [doc.get_annotation_by_id(ann) for ann in doc.segments["SENTENCE"]]
    assert len(sentences) == len(expected_sentences)
    for i, (text, spans) in enumerate(expected_sentences):
        assert sentences[i].text == text
        assert sentences[i].spans == spans
