from medkit.core import Origin, generate_id
from medkit.core.text.annotation import TextBoundAnnotation
from medkit.core.text.span import Span
from tests.data_utils import get_text_document


def test_snippet():
    doc = get_text_document("doc1")
    entity = TextBoundAnnotation(
        origin=Origin(processing_id=generate_id()),
        label="disease",
        spans=[Span(739, 755)],
        text="neurofibromatose",
    )
    doc.add_annotation(entity)

    snippet = entity.get_snippet(doc, max_extend_length=49)
    expected = "tats de la suspicion de neurofibromatose, je proposerai ou pas un"
    assert snippet == expected
