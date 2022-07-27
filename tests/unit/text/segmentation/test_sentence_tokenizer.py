import pytest

from medkit.core import ProvBuilder
from medkit.core.text import Segment, Span
from medkit.text.segmentation import SentenceTokenizer


_TEXT = (
    "Sentence testing the dot. We are testing the carriage return\rthis is the"
    " newline\n Test interrogation ? Now, testing semicolon;Exclamation! Several"
    " punctuation characters?!..."
)


def _get_clean_text_segment(text):
    return Segment(
        label="clean_text",
        spans=[Span(0, len(text))],
        text=text,
    )


TEST_CONFIG = [
    # basic
    (
        SentenceTokenizer(),
        _TEXT,
        [
            ("Sentence testing the dot", [Span(start=0, end=24)]),
            ("We are testing the carriage return", [Span(start=26, end=60)]),
            ("this is the newline", [Span(start=61, end=80)]),
            ("Test interrogation ", [Span(start=82, end=101)]),
            ("Now, testing semicolon", [Span(start=103, end=125)]),
            ("Exclamation", [Span(start=126, end=137)]),
            ("Several punctuation characters", [Span(start=139, end=169)]),
        ],
    ),
    # keep punct chars in sentence
    (
        SentenceTokenizer(keep_punct=True),
        _TEXT,
        [
            ("Sentence testing the dot.", [Span(start=0, end=25)]),
            ("We are testing the carriage return\r", [Span(start=26, end=61)]),
            ("this is the newline\n", [Span(start=61, end=81)]),
            ("Test interrogation ?", [Span(start=82, end=102)]),
            ("Now, testing semicolon;", [Span(start=103, end=126)]),
            ("Exclamation!", [Span(start=126, end=138)]),
            ("Several punctuation characters?!...", [Span(start=139, end=174)]),
        ],
    ),
    # multiline sentences (don't split on \r and \n)
    (
        SentenceTokenizer(punct_chars=(".", ";", "?", "!")),
        "This is a multiline\nsentence! This is another\nmultiline sentence.",
        [
            ("This is a multiline\nsentence", [Span(start=0, end=28)]),
            ("This is another\nmultiline sentence", [Span(start=30, end=64)]),
        ],
    ),
    # trailing sentence with no final punct char
    (
        SentenceTokenizer(),
        "This is a sentence. This is a trailing sentence with no punct",
        [
            ("This is a sentence", [Span(start=0, end=18)]),
            ("This is a trailing sentence with no punct", [Span(start=20, end=61)]),
        ],
    ),
]


@pytest.mark.parametrize(
    "sentence_tokenizer,text,expected_sentences",
    TEST_CONFIG,
    ids=["default", "keep_punct", "multiline", "trailing"],
)
def test_run(sentence_tokenizer, text, expected_sentences):
    clean_text_segment = _get_clean_text_segment(text)
    sentences = sentence_tokenizer.run([clean_text_segment])

    assert len(sentences) == len(expected_sentences)
    for i, (text, spans) in enumerate(expected_sentences):
        assert sentences[i].text == text
        assert sentences[i].spans == spans


def test_prov():
    clean_text_segment = _get_clean_text_segment(
        "This is a sentence. This is another sentence."
    )

    tokenizer = SentenceTokenizer()
    prov_builder = ProvBuilder()
    tokenizer.set_prov_builder(prov_builder)
    sentences = tokenizer.run([clean_text_segment])
    graph = prov_builder.graph

    sentence_1 = sentences[0]
    node_1 = graph.get_node(sentence_1.id)
    assert node_1.data_item_id == sentence_1.id
    assert node_1.operation_id == tokenizer.id
    assert node_1.source_ids == [clean_text_segment.id]

    sentence_2 = sentences[1]
    node_2 = graph.get_node(sentence_2.id)
    assert node_2.data_item_id == sentence_2.id
    assert node_2.operation_id == tokenizer.id
    assert node_2.source_ids == [clean_text_segment.id]
