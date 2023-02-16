from medkit.core.text.annotation import Segment, Entity
from medkit.core.text.span import Span
from medkit.core.text.normalization import EntityNormalization
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
    """Test normalization helpers"""

    entity = Entity(
        label="disease",
        spans=[Span(739, 755)],
        text="neurofibromatose",
    )

    norm = EntityNormalization(kb_name="ICD", kb_id="9540/0", kb_version="10")
    entity.add_norm(norm)

    # should create an Attribute with Entity.NORM_LABEL as label
    # and the EntityNormalization object as value
    norm_attrs = entity.attrs.get(label=Entity.NORM_LABEL)
    assert len(norm_attrs) == 1
    assert norm_attrs[0].value == norm

    # EntityNormalization object should be returned by entity.get_norms()
    norms = entity.get_norms()
    assert len(norms) == 1
    assert norms[0] == norm
