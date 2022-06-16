import pytest

from medkit.core import Attribute, ProvBuilder
from medkit.core.text import Segment, Span
from medkit.text.ner.regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
)

_TEXT = "The patient has asthma and type 1 diabetes."


def _get_sentence_segment(text=_TEXT):
    return Segment(
        label="sentence",
        spans=[Span(0, len(text))],
        text=text,
    )


def test_single_match():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "Diabetes"
    assert entity.text == "diabetes"
    assert entity.spans == [Span(34, 42)]
    assert entity.metadata["rule_id"] == "id_regexp_diabetes"
    assert entity.metadata["version"] == "1"


def test_multiple_matches():
    sentence = _get_sentence_segment()

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
    matcher = RegexpMatcher(rules=[rule_1, rule_2])
    entities = matcher.run([sentence])

    assert len(entities) == 2

    # 1st entity (diabetes)
    entity_1 = entities[0]
    assert entity_1.label == "Diabetes"
    assert entity_1.text == "diabetes"
    assert entity_1.spans == [Span(34, 42)]
    assert entity_1.metadata["rule_id"] == "id_regexp_diabetes"
    assert entity_1.metadata["version"] == "1"

    # 2d entity (asthma)
    entity_2 = entities[1]
    assert entity_2.label == "Asthma"
    assert entity_2.text == "asthma"
    assert entity_2.spans == [Span(16, 22)]
    assert entity_2.metadata["rule_id"] == "id_regexp_asthma"
    assert entity_2.metadata["version"] == "1"


def test_normalization():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
        normalizations=[RegexpMatcherNormalization("umls", "2020AB", "C0011849")],
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    entity = entities[0]
    assert entity.label == "Diabetes"

    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == "C0011849"


def test_exclusion_regex():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        exclusion_regexp="type 1 diabetes",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 0


def test_case_sensitivity_off():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="DIABETES",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "Diabetes"


def test_case_sensitivity_on():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="DIABETES",
        version="1",
        case_sensitive=True,
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 0


def test_case_sensitivity_exclusion_on():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        exclusion_regexp="TYPE 1 DIABETES",
        case_sensitive=True,
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "Diabetes"


def test_unicode_sensitive_off():
    sentence = _get_sentence_segment("Le patient fait du diabète")

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabete",
        version="1",
        unicode_sensitive=False,
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "Diabetes"

    sentence_with_ligatures = _get_sentence_segment(
        "Il a une sœur atteinte de diabète et pensait que sa mère avait peut-être aussi"
        " le diabète. "
    )
    with pytest.raises(ValueError):
        matcher.run([sentence_with_ligatures])


def test_unicode_sensitive_on():
    sentence = _get_sentence_segment("Le patient fait du diabète")

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabete",
        version="1",
        unicode_sensitive=True,
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 0


def test_attrs_to_copy():
    sentence = _get_sentence_segment()
    # copied attribute
    sentence.attrs.append(Attribute(label="negation", value=True))
    # uncopied attribute
    sentence.attrs.append(Attribute(label="hypothesis", value=True))

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
    )

    matcher = RegexpMatcher(
        rules=[rule],
        attrs_to_copy=["negation"],
    )
    entity = matcher.run([sentence])[0]

    # only negation attribute was copied
    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "negation" and attr.value is True


def test_default_rules():
    sentence = _get_sentence_segment()

    # make sure default rules can be loaded and executed
    matcher = RegexpMatcher()
    _ = matcher.run([sentence])


def test_prov():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
        normalizations=[RegexpMatcherNormalization("umls", "2020AB", "C0011849")],
    )
    matcher = RegexpMatcher(rules=[rule])

    prov_builder = ProvBuilder()
    matcher.set_prov_builder(prov_builder)
    entities = matcher.run([sentence])
    graph = prov_builder.graph

    entity = entities[0]
    entity_node = graph.get_node(entity.id)
    assert entity_node.data_item_id == entity.id
    assert entity_node.operation_id == matcher.id
    assert entity_node.source_ids == [sentence.id]

    attr = entity.attrs[0]
    attr_node = graph.get_node(attr.id)
    assert attr_node.data_item_id == attr.id
    assert attr_node.operation_id == matcher.id
    assert attr_node.source_ids == [sentence.id]
