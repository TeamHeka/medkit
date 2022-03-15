import pytest

from medkit.core import Collection
from medkit.core.text import TextDocument, Span
from medkit.text.ner.regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
)

TEXT = "The patient has asthma and type 1 diabetes."


@pytest.fixture
def doc():
    return TextDocument(text=TEXT)


@pytest.fixture
def collection(doc):
    return Collection([doc])


def _find_entity_with_label(doc, label):
    entity_ids = doc.entities.get(label, [])
    if len(entity_ids) == 0:
        return None
    return doc.get_annotation_by_id(entity_ids[0])


def test_single_match(doc):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
    )
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule])
    matcher.annotate_document(doc)

    entity = _find_entity_with_label(doc, "Diabetes")
    assert entity is not None
    assert entity.text == "diabetes"
    assert entity.spans == [Span(34, 42)]
    assert entity.metadata["id_regexp"] == "id_regexp_diabetes"
    assert entity.metadata["version"] == "1"


def test_multiple_matches(doc):
    rule_1 = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
    )
    rule_2 = RegexpMatcherRule(
        id="id_regexp_asthma",
        label="Asthma",
        regexp="asthma",
        version="1",
    )
    matcher = RegexpMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule_1, rule_2]
    )
    matcher.annotate_document(doc)

    entity_1 = _find_entity_with_label(doc, "Diabetes")
    assert entity_1 is not None
    assert entity_1.text == "diabetes"
    assert entity_1.spans == [Span(34, 42)]
    assert entity_1.metadata["id_regexp"] == "id_regexp_diabetes"
    assert entity_1.metadata["version"] == "1"

    entity_2 = _find_entity_with_label(doc, "Asthma")
    assert entity_2 is not None
    assert entity_2.text == "asthma"
    assert entity_2.spans == [Span(16, 22)]
    assert entity_2.metadata["id_regexp"] == "id_regexp_asthma"
    assert entity_2.metadata["version"] == "1"


def test_normalization(doc):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
        normalizations=[RegexpMatcherNormalization("umls", "2020AB", "C0011849")],
    )
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule])
    matcher.annotate_document(doc)

    entity = _find_entity_with_label(doc, "Diabetes")
    assert entity is not None

    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == "C0011849"


def test_exclusion_regex(doc):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        regexp_exclude="type 1 diabetes",
        version="1",
    )
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule])
    matcher.annotate_document(doc)

    assert _find_entity_with_label(doc, "Diabetes") is None


def test_case_sensitivity_off(doc):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="DIABETES",
        version="1",
    )
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule])
    matcher.annotate_document(doc)

    assert _find_entity_with_label(doc, "Diabetes") is not None


def test_case_sensitivity_on(doc):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="DIABETES",
        version="1",
        case_sensitive=True,
    )
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule])
    matcher.annotate_document(doc)

    assert _find_entity_with_label(doc, "Diabetes") is None


def test_case_sensitivity_exclusion_on(doc):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        regexp_exclude="TYPE 1 DIABETES",
        case_sensitive=True,
        version="1",
    )
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule])
    matcher.annotate_document(doc)

    assert _find_entity_with_label(doc, "Diabetes") is not None


def test_annotate_collection(collection):
    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
    )
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL, rules=[rule])
    matcher.annotate(collection)
    doc = collection.documents[0]
    assert _find_entity_with_label(doc, "Diabetes") is not None


def test_default_rules(collection):
    # make sure default rules can be loaded and executed
    matcher = RegexpMatcher(input_label=TextDocument.RAW_TEXT_LABEL)
    matcher.annotate(collection)
