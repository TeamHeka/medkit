from medkit.core.text.annotation import Entity
from medkit.core.text.span import Span
from medkit.core.text.entity_norm_attribute import EntityNormAttribute


def test_normalization():
    """Test normalization helper"""

    entity = Entity(
        label="disease",
        spans=[Span(739, 755)],
        text="neurofibromatose",
    )

    norm = EntityNormAttribute(kb_name="ICD", kb_id="9540/0", kb_version="10")
    entity.attrs.add(norm)

    # EntityNormAttribute object should be returned by entity.attrs.get_norms()
    norms = entity.attrs.get_norms()
    assert len(norms) == 1
    assert norms[0] == norm
