import pytest

from medkit.core import Attribute, generate_id
from medkit.core.text.document import TextDocument
from medkit.core.text.annotation import Entity, Relation, Segment
from medkit.core.text.span import Span


@pytest.fixture()
def init_data():
    doc = TextDocument(text="")
    attribute = Attribute(label="Negation")
    ent1 = Entity(label="ent1", spans=[Span(0, 0)], text="", attrs=[attribute])
    ent2 = Entity(label="ent2", spans=[Span(0, 0)], text="")
    segment = Segment(label="seg1", spans=[Span(0, 0)], text="")
    relation = Relation(label="toto", source_id=ent1.uid, target_id=ent2.uid)
    return doc, ent1, ent2, segment, relation, attribute


def test_add_annotation(init_data):
    doc, ent1, ent2, segment, relation, attribute = init_data
    # Test entity addition in entity list
    doc.add_annotation(ent1)
    assert ent1 in doc.get_entities()
    # Test exception when adding the same annotation
    with pytest.raises(ValueError):
        doc.add_annotation(ent1)
    # Test segment addition
    doc.add_annotation(segment)
    assert segment in doc.get_segments()
    # Test relation addition in annotations list
    doc.add_annotation(ent2)
    doc.add_annotation(relation)
    assert doc.get_annotation_by_id(relation.uid) == relation


def test_get_annotations_by_key(init_data):
    doc, ent1, ent2, segment, relation, attribute = init_data
    ent1.add_key(key="superkey")
    doc.add_annotation(ent1)
    assert doc.get_annotations_by_key(key="superkey") == [ent1]
    assert doc.get_annotations_by_key(key="hello") == []


def test_get_annotations_by_label(init_data):
    doc, ent1, ent2, segment, relation, attribute = init_data
    doc.add_annotation(ent1)
    doc.add_annotation(ent2)

    assert doc.get_annotations_by_label(ent1.label) == [ent1]
    assert doc.get_annotations_by_label(ent1.label)[0].attrs.get() == [attribute]
    assert doc.get_annotations_by_label(ent2.label) == [ent2]

    # add 2d annotation for same label and make sure we find all annotations
    # for that label
    ent3 = Entity(label=ent1.label, spans=[Span(0, 0)], text="")
    doc.add_annotation(ent3)
    assert doc.get_annotations_by_label(ent1.label) == [ent1, ent3]


def test_raw_segment():
    # raw text segment automatically generated
    text = "This is the raw text."
    doc = TextDocument(text=text)
    seg = doc.raw_segment
    assert seg is not None
    assert seg.label == TextDocument.RAW_LABEL
    assert seg.text == text
    assert seg.spans == [Span(0, len(text))]

    # also reachable through label and uid
    assert doc.get_annotations_by_label(TextDocument.RAW_LABEL) == [seg]
    assert doc.get_annotation_by_id(seg.uid) is seg
    # but not included in full annotation list
    assert seg not in doc.get_annotations()

    # docs with same ids should have raw text segments with same uid
    uid = generate_id()
    doc_1 = TextDocument(uid=uid, text=text)
    ann_1 = doc_1.get_annotations_by_label(TextDocument.RAW_LABEL)[0]
    doc_2 = TextDocument(uid=uid, text=text)
    ann_2 = doc_2.get_annotations_by_label(TextDocument.RAW_LABEL)[0]
    assert ann_1.uid == ann_2.uid

    # manually adding annotation with reserved label RAW_LABEL is forbidden
    doc = TextDocument(text=text)
    seg = Segment(label=TextDocument.RAW_LABEL, spans=Span(0, len(text)), text=text)
    with pytest.raises(
        RuntimeError, match=r"Cannot add annotation with reserved label .*"
    ):
        doc.add_annotation(seg)
