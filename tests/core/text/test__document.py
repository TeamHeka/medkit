import pytest

from medkit.core.text.document import TextDocument
from medkit.core.text.annotation import Entity, Relation, Attribute


def test_add_annotation():
    doc = TextDocument(text="hello")
    ent1 = Entity(ann_source="", label="ent1", spans="", text="")
    ent2 = Entity(ann_source="", label="ent2", spans="", text="")
    relation = Relation(ann_source="", label="toto", source_id=ent1.id, target_id=ent2.id)
    attribute = Attribute(ann_source="", label="Negation", target_id=ent1.id)
    # Test entity addition in entity list
    doc.add_annotation(ent1)
    assert ent1.id in doc.entities.get(ent1.label)
    # Test exception when adding the same annotation
    with pytest.raises(ValueError):
        doc.add_annotation(ent1)
    # Test relation addition in annotations list
    doc.add_annotation(ent2)
    doc.add_annotation(relation)
    assert doc.get_annotation_by_id(relation.id) == relation
    # Test attribute addition in attributes list
    doc.add_annotation(attribute)
    assert attribute.id in doc.attributes.get(attribute.target_id)
