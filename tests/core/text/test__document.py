import pytest

from medkit.core import Origin
from medkit.core.text.document import TextDocument
from medkit.core.text.annotation import Entity, Relation, Attribute
from medkit.core.text.span import Span


@pytest.fixture()
def init_data():
    doc = TextDocument()
    ent1 = Entity(origin=Origin(), label="ent1", spans=[Span(0, 0)], text="")
    ent2 = Entity(origin=Origin(), label="ent2", spans=[Span(0, 0)], text="")
    relation = Relation(
        origin=Origin(), label="toto", source_id=ent1.id, target_id=ent2.id
    )
    attribute = Attribute(origin=Origin(), label="Negation", target_id=ent1.id)
    return doc, ent1, ent2, relation, attribute


def test_add_annotation(init_data):
    doc, ent1, ent2, relation, attribute = init_data
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


def test_get_attributes_by_annotation(init_data):
    doc, ent1, ent2, relation, attribute = init_data
    doc.add_annotation(ent1)
    doc.add_annotation(attribute)
    ent1_attributes = doc.get_attributes_by_annotation(ent1.id)
    assert attribute.label in ent1_attributes.keys()
    assert ent1_attributes[attribute.label] is attribute
