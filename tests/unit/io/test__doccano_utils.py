from medkit.io._doccano_utils import (
    DoccanoDocRelationExtraction,
    DoccanoDocTextClassification,
    DoccanoDocSeqLabeling,
    DoccanoEntity,
    DoccanoRelation,
    DoccanoEntityTuple,
)


def test_doc_relation_extraction_from_dict():
    test_line = {
        "text": "medkit was created in 2022",
        "entities": [
            {"id": 0, "start_offset": 0, "end_offset": 6, "label": "ORG"},
            {"id": 1, "start_offset": 22, "end_offset": 26, "label": "DATE"},
        ],
        "relations": [{"id": 0, "from_id": 0, "to_id": 1, "type": "created_in"}],
    }
    doc = DoccanoDocRelationExtraction.from_dict(
        test_line, column_text="text", count_CRLF_character_as_one=False
    )
    assert len(doc.entities) == 2
    assert len(doc.relations) == 1

    entity = DoccanoEntity(id=0, start_offset=0, end_offset=6, label="ORG")
    assert entity in doc.entities
    relation = DoccanoRelation(id=0, from_id=0, to_id=1, type="created_in")
    assert relation in doc.relations


def test_doc_seq_labeling_from_dict():
    test_line = {
        "text": "medkit was created in 2022",
        "label": [(0, 6, "ORG"), (22, 26, "DATE")],
    }

    doc = DoccanoDocSeqLabeling.from_dict(
        test_line, column_text="text", column_label="label"
    )
    assert len(doc.entities) == 2
    entity = DoccanoEntityTuple(start_offset=0, end_offset=6, label="ORG")
    assert entity in doc.entities


def test_doc_text_classification_from_dict():
    test_line = {"text": "medkit was created in 2022", "label": ["header"]}
    doc = DoccanoDocTextClassification.from_dict(
        test_line, column_text="text", column_label="label"
    )
    assert doc.label == "header"
