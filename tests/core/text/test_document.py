import pytest
import uuid

from medkit.core import Origin
from medkit.core.text.document import TextDocument
from medkit.core.text.annotation import Entity, Relation, Attribute, TextBoundAnnotation
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
    assert ent1_attributes[attribute.label][0] is attribute


def test_get_annotations_by_label(init_data):
    doc, ent1, ent2, relation, attribute = init_data
    doc.add_annotation(ent1)
    doc.add_annotation(ent2)
    doc.add_annotation(attribute)

    assert doc.get_annotations_by_label(ent1.label) == [ent1]
    assert doc.get_annotations_by_label(ent2.label) == [ent2]
    assert doc.get_annotations_by_label(attribute.label) == [attribute]

    # add 2d annotation for same label and make sure we find all annotations
    # for that label
    ent3 = Entity(origin=Origin(), label=ent1.label, spans=[Span(0, 0)], text="")
    doc.add_annotation(ent3)
    assert doc.get_annotations_by_label(ent1.label) == [ent1, ent3]


def test_raw_text_annotation():
    text = "This is the raw text."
    # raw text ann automatically generated when text is provided
    doc = TextDocument(text=text)
    anns = doc.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)
    assert len(anns) == 1
    ann = anns[0]
    assert ann.label == TextDocument.RAW_TEXT_LABEL
    assert ann.text == doc.text
    assert type(ann) == TextBoundAnnotation

    # no raw text ann if no text provided
    doc = TextDocument()
    anns = doc.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)
    assert len(anns) == 0

    # docs with same ids should have raw text anns with same id
    doc_id = uuid.uuid1()
    doc_1 = TextDocument(doc_id=doc_id, text=text)
    ann_1 = doc_1.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)[0]
    doc_2 = TextDocument(doc_id=doc_id, text=text)
    ann_2 = doc_2.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)[0]
    assert ann_1.id == ann_2.id
