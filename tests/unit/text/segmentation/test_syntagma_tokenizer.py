import pytest

from medkit.core import ProvBuilder
from medkit.core.text import Segment, Span
from medkit.text.segmentation import SyntagmaTokenizer

_TEXT = (
    " Elle avait été améliorée par l'intervention pratiquée par le chirurgien mais"
    " présentait des petites douleurs résiduelles sur la face interne du genou"
    " droit"
)
TEST_CONFIG = [
    (
        SyntagmaTokenizer.get_example(),
        [
            {
                "spans": [Span(start=1, end=72)],
                "text": (
                    "Elle avait été améliorée par l'intervention pratiquée par le"
                    " chirurgien"
                ),
            },
            {
                "spans": [Span(start=72, end=156)],
                "text": (
                    " mais présentait des petites douleurs résiduelles sur la face"
                    " interne du genou droit"
                ),
            },
        ],
    ),
    (
        SyntagmaTokenizer.get_example(keep_separator=False),
        [
            {
                "spans": [Span(start=1, end=72)],
                "text": (
                    "Elle avait été améliorée par l'intervention pratiquée par le"
                    " chirurgien"
                ),
            },
            {
                "spans": [Span(start=78, end=156)],
                "text": (
                    "présentait des petites douleurs résiduelles sur la face"
                    " interne du genou droit"
                ),
            },
        ],
    ),
]


def _get_segment_from_text(text=_TEXT):
    return Segment(
        label="segment",
        spans=[Span(0, len(text))],
        text=text,
    )


@pytest.mark.parametrize("syntagma_tokenizer, expected_syntagmas", TEST_CONFIG)
def test_run(syntagma_tokenizer, expected_syntagmas):
    segment = _get_segment_from_text()

    syntagmas = syntagma_tokenizer.run([segment])
    assert len(syntagmas) == 2
    for i, expected in enumerate(expected_syntagmas):
        assert syntagmas[i].label == "SYNTAGMA"
        assert syntagmas[i].spans == expected["spans"]
        assert syntagmas[i].text == expected["text"]


def test_prov():
    segment = _get_segment_from_text()

    tokenizer = SyntagmaTokenizer.get_example()
    prov_builder = ProvBuilder()
    tokenizer.set_prov_builder(prov_builder)
    syntagmas = tokenizer.run([segment])
    graph = prov_builder.graph

    syntagma_1 = syntagmas[0]
    node_1 = graph.get_node(syntagma_1.id)
    assert node_1.data_item_id == syntagma_1.id
    assert node_1.operation_id == tokenizer.id
    assert node_1.source_ids == [segment.id]

    syntagma_2 = syntagmas[1]
    node_2 = graph.get_node(syntagma_2.id)
    assert node_2.data_item_id == syntagma_2.id
    assert node_2.operation_id == tokenizer.id
    assert node_2.source_ids == [segment.id]
