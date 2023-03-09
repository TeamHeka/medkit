from medkit.core.text.annotation import Segment, Entity
from medkit.core.text.span import Span
from medkit.core.text.entity_norm_attribute import EntityNormAttribute
from tests.data_utils import get_text_document


def test_snippet():
    doc = get_text_document("doc1")
    entity = Segment(
        label="disease",
        spans=[Span(739, 755)],
        text="neurofibromatose",
    )
    doc.anns.add(entity)

    snippet = entity.get_snippet(doc, max_extend_length=49)
    expected = "tats de la suspicion de neurofibromatose, je proposerai ou pas un"
    assert snippet == expected


def test_normalization():
    """Test normalization helper"""

    entity = Entity(
        label="disease",
        spans=[Span(739, 755)],
        text="neurofibromatose",
    )

    norm = EntityNormAttribute(kb_name="ICD", kb_id="9540/0", kb_version="10")
    entity.attrs.add(norm)

    # EntityNormAttribute object should be returned by entity.get_norm_attrs()
    norms = entity.get_norm_attrs()
    assert len(norms) == 1
    assert norms[0] == norm
