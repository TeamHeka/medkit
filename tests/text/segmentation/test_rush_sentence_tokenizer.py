import pytest

from medkit.core import Origin
from medkit.core.text import Segment, Span, ModifiedSpan
from medkit.text.segmentation.rush_sentence_tokenizer import RushSentenceTokenizer


TEST_CONFIG = [
    (
        "Sentence testing the dot. Newlines\ndo not split. Test"
        " interrogation? Semicolon; and exclamation marks! do not split",
        RushSentenceTokenizer(input_label="clean_text"),
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
        RushSentenceTokenizer(input_label="clean_text", keep_newlines=False),
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


def _get_clean_text_segment(text):
    return Segment(
        origin=Origin(),
        label="clean_text",
        spans=[Span(0, len(text))],
        text=text,
    )


@pytest.mark.parametrize(
    "text,sentence_tokenizer,expected_sentences",
    TEST_CONFIG,
    ids=["default", "keep_newlines"],
)
def test_default_rules(text, sentence_tokenizer, expected_sentences):
    clean_text_segment = _get_clean_text_segment(text)

    sentences = sentence_tokenizer.process([clean_text_segment])
    assert len(sentences) == len(expected_sentences)
    for i, (text, spans) in enumerate(expected_sentences):
        assert sentences[i].text == text
        assert sentences[i].spans == spans
