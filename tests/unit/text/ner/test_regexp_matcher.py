import logging

from medkit.core import Attribute, ProvTracer
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


def test_single_rule():
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


def test_multiple_rules():
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


def test_multiple_rules_no_id():
    sentence = _get_sentence_segment()

    rule_1 = RegexpMatcherRule(label="Diabetes", regexp="diabetes")
    rule_2 = RegexpMatcherRule(label="Asthma", regexp="asthma")
    matcher = RegexpMatcher(rules=[rule_1, rule_2])
    entities = matcher.run([sentence])

    assert len(entities) == 2

    # entities have corresponding rule index as rule_id metadta
    entity_1 = entities[0]
    assert entity_1.metadata["rule_id"] == 0
    entity_2 = entities[1]
    assert entity_2.metadata["rule_id"] == 1


def test_normalization():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        label="Diabetes",
        regexp="diabetes",
        normalizations=[RegexpMatcherNormalization("umls", "2020AB", "C0011849")],
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    entity = entities[0]
    assert entity.label == "Diabetes"

    attrs = entity.get_attrs_by_label("umls")
    assert len(attrs) == 1
    attr = attrs[0]
    assert attr.label == "umls"
    assert attr.value == "C0011849"


def test_exclusion_regex():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        label="Diabetes", regexp="diabetes", exclusion_regexp="type 1 diabetes"
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 0


def test_case_sensitivity_off():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(label="Diabetes", regexp="DIABETES")
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "Diabetes"


def test_case_sensitivity_on():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(label="Diabetes", regexp="DIABETES", case_sensitive=True)
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 0


def test_case_sensitivity_exclusion_on():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        label="Diabetes",
        regexp="diabetes",
        exclusion_regexp="TYPE 1 DIABETES",
        case_sensitive=True,
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "Diabetes"


def test_unicode_sensitive_off(caplog):
    sentence = _get_sentence_segment("Le patient fait du diabète")

    rule = RegexpMatcherRule(
        label="Diabetes", regexp="diabete", unicode_sensitive=False
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
    with caplog.at_level(logging.WARNING, logger="medkit.text.ner.regexp_matcher"):
        matcher.run([sentence_with_ligatures])
        assert len(caplog.messages) == 1


def test_unicode_sensitive_on():
    sentence = _get_sentence_segment("Le patient fait du diabète")

    rule = RegexpMatcherRule(label="Diabetes", regexp="diabete", unicode_sensitive=True)
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 0


def test_attrs_to_copy():
    sentence = _get_sentence_segment()
    # copied attribute
    sentence.add_attr(Attribute(label="negation", value=True))
    # uncopied attribute
    sentence.add_attr(Attribute(label="hypothesis", value=True))

    rule = RegexpMatcherRule(label="Diabetes", regexp="diabetes")

    matcher = RegexpMatcher(
        rules=[rule],
        attrs_to_copy=["negation"],
    )
    entity = matcher.run([sentence])[0]

    # only negation attribute was copied
    neg_attrs = entity.get_attrs_by_label("negation")
    assert len(neg_attrs) == 1 and neg_attrs[0].value is True
    assert len(entity.get_attrs_by_label("hypothesis")) == 0


def test_default_rules():
    sentence = _get_sentence_segment()

    # make sure default rules can be loaded and executed
    matcher = RegexpMatcher()
    _ = matcher.run([sentence])


def test_prov():
    sentence = _get_sentence_segment()

    normalization = RegexpMatcherNormalization("umls", "2020AB", "C0011849")
    rule = RegexpMatcherRule(
        label="Diabetes", regexp="diabetes", normalizations=[normalization]
    )
    matcher = RegexpMatcher(rules=[rule])

    prov_tracer = ProvTracer()
    matcher.set_prov_tracer(prov_tracer)
    entities = matcher.run([sentence])

    entity = entities[0]
    entity_prov = prov_tracer.get_prov(entity.id)
    assert entity_prov.data_item == entity
    assert entity_prov.op_desc == matcher.description
    assert entity_prov.source_data_items == [sentence]

    attr = entity.get_attrs_by_label("umls")[0]
    attr_prov = prov_tracer.get_prov(attr.id)
    assert attr_prov.data_item == attr
    assert attr_prov.op_desc == matcher.description
    assert attr_prov.source_data_items == [sentence]
