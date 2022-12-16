from typing import Dict, Any

from medkit.core import Annotation, DictStore
from medkit.core.document import Document


class _MockAnnotation(Annotation):
    def __init__(self, label, value, keys=None, uid=None):
        super().__init__(label=label, keys=keys, uid=uid)
        self.value = value

    @classmethod
    def from_dict(cls, annotation_dict: Dict[str, Any]) -> Annotation:
        pass


def test_basic():
    "Basic usage, add annotations and retrieve them"

    doc = Document()
    ann_1 = _MockAnnotation("name", "Bob")
    doc.add_annotation(ann_1)
    ann_2 = _MockAnnotation("topic", "Cancer")
    doc.add_annotation(ann_2)
    ann_3 = _MockAnnotation("topic", "Chemotherapy")
    doc.add_annotation(ann_3)

    assert set(doc.get_annotations()) == {ann_1, ann_2, ann_3}
    assert doc.get_annotation_by_id(ann_1.uid) == ann_1
    assert doc.get_annotations_by_label("name") == [ann_1]
    assert doc.get_annotations_by_label("topic") == [ann_2, ann_3]
    assert doc.get_annotations_by_label("misc") == []


def test_keys():
    """Retrieve annotations by keys"""

    doc = Document()
    ann_1 = _MockAnnotation("name", "Bob", keys=["names"])
    doc.add_annotation(ann_1)
    ann_2 = _MockAnnotation("topic", "Cancer", keys=["topics", "regexp_matches"])
    doc.add_annotation(ann_2)
    ann_3 = _MockAnnotation("topic", "Chemotherapy", keys=["topics", "umls_matches"])
    doc.add_annotation(ann_3)

    assert doc.get_annotations_by_key("names") == [ann_1]
    assert doc.get_annotations_by_key("topics") == [ann_2, ann_3]
    assert doc.get_annotations_by_key("regexp_matches") == [ann_2]
    assert doc.get_annotations_by_key("umls_matches") == [ann_3]
    assert doc.get_annotations_by_label("misc") == []


def test_store():
    """Init doc with own private store or shared store"""

    doc_1 = Document()
    assert doc_1.has_shared_store is False

    store = DictStore()
    doc_2 = Document(store=store)
    assert doc_2.store is store
    assert doc_2.has_shared_store is True
