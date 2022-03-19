from medkit.core.text.annotation import Segment
from medkit.core.text.span import Span
from tests.data_utils import get_text_document


def test_snippet():
    doc = get_text_document("doc1")
    entity = Segment(
        label="disease",
        spans=[Span(739, 755)],
        text="neurofibromatose",
    )
    doc.add_annotation(entity)

    snippet = entity.get_snippet(doc, max_extend_length=49)
    expected = "tats de la suspicion de neurofibromatose, je proposerai ou pas un"
    assert snippet == expected
