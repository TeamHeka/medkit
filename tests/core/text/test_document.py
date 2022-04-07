import pytest

from medkit.core import Attribute, generate_id
from medkit.core.text.document import TextDocument
from medkit.core.text.annotation import Entity, Relation, Segment
from medkit.core.text.span import Span


@pytest.fixture()
def init_data():
    doc = TextDocument()
    attribute = Attribute(label="Negation")
    ent1 = Entity(label="ent1", spans=[Span(0, 0)], text="", attrs=[attribute])
    ent2 = Entity(label="ent2", spans=[Span(0, 0)], text="")
    relation = Relation(label="toto", source_id=ent1.id, target_id=ent2.id)
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


def test_get_annotations_by_label(init_data):
    doc, ent1, ent2, relation, attribute = init_data
    doc.add_annotation(ent1)
    doc.add_annotation(ent2)

    assert doc.get_annotations_by_label(ent1.label) == [ent1]
    assert doc.get_annotations_by_label(ent1.label)[0].attrs == [attribute]
    assert doc.get_annotations_by_label(ent2.label) == [ent2]

    # add 2d annotation for same label and make sure we find all annotations
    # for that label
    ent3 = Entity(label=ent1.label, spans=[Span(0, 0)], text="")
    doc.add_annotation(ent3)
    assert doc.get_annotations_by_label(ent1.label) == [ent1, ent3]


def test_raw_text_segment():
    text = "This is the raw text."
    # raw text segment automatically generated when text is provided
    doc = TextDocument(text=text)
    anns = doc.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)
    assert len(anns) == 1
    ann = anns[0]
    assert ann.label == TextDocument.RAW_TEXT_LABEL
    assert ann.text == doc.text
    assert type(ann) == Segment

    # no raw text segment if no text provided
    doc = TextDocument()
    anns = doc.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)
    assert len(anns) == 0

    # docs with same ids should have raw text segments with same id
    doc_id = generate_id()
    doc_1 = TextDocument(doc_id=doc_id, text=text)
    ann_1 = doc_1.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)[0]
    doc_2 = TextDocument(doc_id=doc_id, text=text)
    ann_2 = doc_2.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)[0]
    assert ann_1.id == ann_2.id
