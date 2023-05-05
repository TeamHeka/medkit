import pytest

from medkit.core import ProvTracer
from medkit.core.text import Segment, Span
from medkit.text.segmentation.syntagma_tokenizer import (
    SyntagmaTokenizer,
    _DEFAULT_SYNTAGMA_DEFINITION_RULES,
)

_TEXT = (
    " Elle avait été améliorée par l'intervention pratiquée par le chirurgien mais"
    " présentait des petites douleurs résiduelles sur la face interne du genou"
    " droit"
)
TEST_CONFIG = [
    # basic
    (
        SyntagmaTokenizer.get_example(),
        _TEXT,
        [
            {
                "spans": [Span(start=1, end=72)],
                "text": (
                    "Elle avait été améliorée par l'intervention pratiquée par le"
                    " chirurgien"
                ),
            },
            {
                "spans": [Span(start=73, end=156)],
                "text": (
                    "mais présentait des petites douleurs résiduelles sur la face"
                    " interne du genou droit"
                ),
            },
        ],
    ),
    # multiline syntagmas (don't split on \r and \n)
    (
        SyntagmaTokenizer(separators=(r"\bmais\b",)),
        "Elle avait été\naméliorée mais présentait des douleurs",
        [
            {
                "spans": [Span(start=0, end=24)],
                "text": "Elle avait été\naméliorée",
            },
            {
                "spans": [Span(start=25, end=53)],
                "text": "mais présentait des douleurs",
            },
        ],
    ),
]


def _get_segment_from_text(text):
    return Segment(
        label="segment",
        spans=[Span(0, len(text))],
        text=text,
    )


@pytest.mark.parametrize("syntagma_tokenizer, text, expected_syntagmas", TEST_CONFIG)
def test_run(syntagma_tokenizer, text, expected_syntagmas):
    segment = _get_segment_from_text(text)

    syntagmas = syntagma_tokenizer.run([segment])
    assert len(syntagmas) == len(expected_syntagmas)
    for i, expected in enumerate(expected_syntagmas):
        assert syntagmas[i].label == "SYNTAGMA"
        assert syntagmas[i].spans == expected["spans"]
        assert syntagmas[i].text == expected["text"]


def test_prov():
    segment = _get_segment_from_text(_TEXT)

    tokenizer = SyntagmaTokenizer.get_example()
    prov_tracer = ProvTracer()
    tokenizer.set_prov_tracer(prov_tracer)
    syntagmas = tokenizer.run([segment])

    syntagma_1 = syntagmas[0]
    prov_1 = prov_tracer.get_prov(syntagma_1.uid)
    assert prov_1.data_item == syntagma_1
    assert prov_1.op_desc == tokenizer.description
    assert prov_1.source_data_items == [segment]

    syntagma_2 = syntagmas[1]
    prov_2 = prov_tracer.get_prov(syntagma_2.uid)
    assert prov_2.data_item == syntagma_2
    assert prov_2.op_desc == tokenizer.description
    assert prov_2.source_data_items == [segment]


def test_syntagma_def_file_encoding_error():
    with pytest.raises(UnicodeError):
        SyntagmaTokenizer.load_syntagma_definition(
            filepath=_DEFAULT_SYNTAGMA_DEFINITION_RULES, encoding="utf-16"
        )
