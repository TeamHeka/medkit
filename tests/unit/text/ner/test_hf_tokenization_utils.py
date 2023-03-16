from pathlib import Path
import pytest

from medkit.text.ner.hf_tokenization_utils import (
    transform_entities_to_tags,
    align_and_map_tokens_with_tags,
    convert_labels_to_tags,
    SPECIAL_TAG_ID_HF,
)

pytest.importorskip(modname="torch", reason="torch is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")

from transformers import BertTokenizerFast  # noqa: E402
from medkit.core.text import Segment, Entity, Span  # noqa: E402

_PATH_TO_VOCAB_FILE = Path(__file__).parent / "dummy_hf_vocab" / "vocab.txt"


def _get_segment_entities(offset_span):
    segment = Segment(
        text="medkit is a python library",
        spans=[Span(start=0 + offset_span, end=26 + offset_span)],
        label="SENTENCE",
    )
    entities = [
        Entity(
            label="corporation",
            spans=[Span(start=0 + offset_span, end=6 + offset_span)],
            text="medkit",
        ),
        Entity(
            label="language",
            spans=[Span(start=12 + offset_span, end=18 + offset_span)],
            text="python",
        ),
    ]
    return [segment, entities]


@pytest.fixture()
def tokenizer():
    tokenizer = BertTokenizerFast(_PATH_TO_VOCAB_FILE)
    return tokenizer


TEST_CONFIG = (
    (
        0,
        "bilou",
        ["O", "B-corporation", "L-corporation", "O", "O", "U-language", "O", "O"],
    ),
    (
        10,
        "bilou",
        ["O", "B-corporation", "L-corporation", "O", "O", "U-language", "O", "O"],
    ),
    (
        0,
        "iob2",
        ["O", "B-corporation", "I-corporation", "O", "O", "B-language", "O", "O"],
    ),
    (
        10,
        "iob2",
        ["O", "B-corporation", "I-corporation", "O", "O", "B-language", "O", "O"],
    ),
)


@pytest.mark.parametrize(
    "offset_span,tagging_scheme,expected_tags",
    TEST_CONFIG,
    ids=[
        "span_no_offset_bilou",
        "span_offset_bilou",
        "span_no_offset_no_bilou",
        "span_offset_no_bilou",
    ],
)
def test_transform_entities_offset(
    tokenizer, offset_span, tagging_scheme, expected_tags
):
    # Testing transformation with span starting at 0 and starting in other position
    segment, entities = _get_segment_entities(offset_span=offset_span)
    text_encoding = tokenizer(segment.text).encodings[0]
    tags = transform_entities_to_tags(
        segment=segment,
        entities=entities,
        text_encoding=text_encoding,
        tagging_scheme=tagging_scheme,
    )
    assert tags == expected_tags


def test_transform_entities_no_aligned(tokenizer):
    # Testing aligned between span and entities
    segment, entities = _get_segment_entities(offset_span=10)
    text_encoding = tokenizer(segment.text).encodings[0]

    # entity language starts before span start, ignore entity
    entities[1].spans = [Span(start=5, end=11)]
    tags = transform_entities_to_tags(
        segment=segment, entities=entities, text_encoding=text_encoding
    )
    assert tags == ["O", "B-corporation", "L-corporation", "O", "O", "O", "O", "O"]

    # entity language is offside, ignore entity
    entities[1].spans = [Span(start=40, end=46)]
    tags = transform_entities_to_tags(
        segment=segment, entities=entities, text_encoding=text_encoding
    )
    assert tags == ["O", "B-corporation", "L-corporation", "O", "O", "O", "O", "O"]


def test_aligned_tokens_with_tags(tokenizer):
    text_encoding = tokenizer("medkit").encodings[0]
    tag_mapping = {"O": 0, "B-corporation": 1, "L-corporation": 2}

    tags_to_aligned = ["O", "B-corporation", "L-corporation", "O"]
    # tag all subtokens by word
    tags_ids = align_and_map_tokens_with_tags(
        text_encoding=text_encoding,
        tags=tags_to_aligned,
        tag_to_id=tag_mapping,
        map_sub_tokens=True,
    )
    assert tags_ids == [SPECIAL_TAG_ID_HF, 1, 2, SPECIAL_TAG_ID_HF]

    # tag only the first token by word, recommended
    tags_ids = align_and_map_tokens_with_tags(
        text_encoding=text_encoding,
        tags=tags_to_aligned,
        tag_to_id=tag_mapping,
        map_sub_tokens=False,
    )
    assert tags_ids == [SPECIAL_TAG_ID_HF, 1, SPECIAL_TAG_ID_HF, SPECIAL_TAG_ID_HF]


def test_convert_labels_to_tags():
    tags = convert_labels_to_tags(labels=["procedure"], tagging_scheme="bilou")
    assert tags == {
        "O": 0,
        "B-procedure": 1,
        "I-procedure": 2,
        "L-procedure": 3,
        "U-procedure": 4,
    }
    tags = convert_labels_to_tags(labels=["procedure"], tagging_scheme="iob2")
    assert tags == {
        "O": 0,
        "B-procedure": 1,
        "I-procedure": 2,
    }
