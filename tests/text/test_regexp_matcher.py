import uuid

import pytest

from medkit.core import Collection
from medkit.core.text import TextDocument, TextBoundAnnotation, Span
from medkit.text.ner.regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
)

TEXT = "The patient has asthma and type 1 diabetes."


@pytest.fixture
def collection():
    doc = TextDocument(text=TEXT)
    raw_text = TextBoundAnnotation(
        origin_id=uuid.uuid1(), label="RAW_TEXT", spans=[Span(0, len(TEXT))], text=TEXT
    )
    doc.add_annotation(raw_text)
    return Collection([doc])


def test_simple_match(collection):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
        normalizations=[RegexpMatcherNormalization("umls", "2020AB", "C0001234")],
    )
    matcher = RegexpMatcher(input_label="RAW_TEXT", rules=[rule])

    doc = collection.documents[0]
    nb_anns_before = len(doc.get_annotations())
    matcher.annotate_document(doc)

    anns = doc.get_annotations()
    assert len(anns) == nb_anns_before + 2

    entity = next(a for a in anns if a.label == "Diabetes")
    assert entity.text == "diabetes"
    assert entity.spans == [Span(34, 42)]
    assert entity.metadata["id_regexp"] == "id_regexp_diabetes"
    assert entity.metadata["version"] == "1"

    assert entity.id in doc.attributes
    attribute_ids = doc.attributes[entity.id]
    assert len(attribute_ids) == 1
    attribute = doc.get_annotation_by_id(attribute_ids[0])
    assert attribute.target_id == entity.id
    assert attribute.label == rule.normalizations[0].kb_name
    assert attribute.value == rule.normalizations[0].id


def test_default_rules(collection):
    # make sure default rules can be loaded and executed
    matcher = RegexpMatcher(input_label="RAW_TEXT")
    matcher.annotate(collection)
