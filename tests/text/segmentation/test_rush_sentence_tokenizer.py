import pytest

from medkit.core.text import TextDocument, Span, ModifiedSpan
from medkit.text.segmentation.rush_sentence_tokenizer import RushSentenceTokenizer


TEST_CONFIG = [
    (
        "Sentence testing the dot. Newlines\ndo not split. Test"
        " interrogation? Semicolon; and exclamation marks! do not split",
        RushSentenceTokenizer(input_label=TextDocument.RAW_TEXT_LABEL),
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
        RushSentenceTokenizer(
            input_label=TextDocument.RAW_TEXT_LABEL, keep_newlines=False
        ),
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


@pytest.mark.parametrize(
    "text,sentence_tokenizer,expected_sentences",
    TEST_CONFIG,
    ids=["default", "keep_newlines"],
)
def test_default_rules(text, sentence_tokenizer, expected_sentences):
    assert sentence_tokenizer.input_label == TextDocument.RAW_TEXT_LABEL

    doc = TextDocument(text=text)
    sentence_tokenizer.annotate_document(doc)
    sentences = [doc.get_annotation_by_id(ann) for ann in doc.segments["SENTENCE"]]
    assert len(sentences) == len(expected_sentences)
    for i, (text, spans) in enumerate(expected_sentences):
        assert sentences[i].text == text
        assert sentences[i].spans == spans
