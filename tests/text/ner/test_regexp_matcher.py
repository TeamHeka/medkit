from medkit.core import Origin, Attribute
from medkit.core.text import Segment, Span
from medkit.text.ner.regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
)

_TEXT = "The patient has asthma and type 1 diabetes."


def _get_sentence_segment():
    return Segment(
        origin=Origin(),
        label="sentence",
        spans=[Span(0, len(_TEXT))],
        text=_TEXT,
    )


def _find_entity(entities, label):
    try:
        return next(e for e in entities if e.label == label)
    except StopIteration:
        return None


def test_single_match():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.process([sentence])

    assert len(entities) == 1
    entity = _find_entity(entities, "Diabetes")
    assert entity is not None
    assert entity.text == "diabetes"
    assert entity.spans == [Span(34, 42)]
    assert entity.metadata["id_regexp"] == "id_regexp_diabetes"
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
    entities = matcher.process([sentence])

    assert len(entities) == 2

    entity_1 = _find_entity(entities, "Diabetes")
    assert entity_1 is not None
    assert entity_1.text == "diabetes"
    assert entity_1.spans == [Span(34, 42)]
    assert entity_1.metadata["id_regexp"] == "id_regexp_diabetes"
    assert entity_1.metadata["version"] == "1"

    entity_2 = _find_entity(entities, "Asthma")
    assert entity_2 is not None
    assert entity_2.text == "asthma"
    assert entity_2.spans == [Span(16, 22)]
    assert entity_2.metadata["id_regexp"] == "id_regexp_asthma"
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
    entities = matcher.process([sentence])

    entity = _find_entity(entities, "Diabetes")
    assert entity is not None

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
        regexp_exclude="type 1 diabetes",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.process([sentence])

    assert _find_entity(entities, "Diabetes") is None


def test_case_sensitivity_off():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="DIABETES",
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.process([sentence])

    assert _find_entity(entities, "Diabetes") is not None


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
    entities = matcher.process([sentence])

    assert _find_entity(entities, "Diabetes") is None


def test_case_sensitivity_exclusion_on():
    sentence = _get_sentence_segment()

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        regexp_exclude="TYPE 1 DIABETES",
        case_sensitive=True,
        version="1",
    )
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.process([sentence])

    assert _find_entity(entities, "Diabetes") is not None


def test_attrs_to_copy():
    sentence = _get_sentence_segment()
    sentence.attrs.append(Attribute(origin=Origin(), label="negation", value=True))

    rule = RegexpMatcherRule(
        id="id_regexp_diabetes",
        label="Diabetes",
        regexp="diabetes",
        version="1",
    )

    # attribute not copied
    matcher = RegexpMatcher(rules=[rule])
    entities = matcher.process([sentence])
    entity = _find_entity(entities, "Diabetes")
    assert not entity.attrs

    # attribute copied
    matcher = RegexpMatcher(
        rules=[rule],
        attrs_to_copy=["negation"],
    )
    entities = matcher.process([sentence])
    entity = _find_entity(entities, "Diabetes")
    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "negation" and attr.value is True


def test_default_rules():
    sentence = _get_sentence_segment()

    # make sure default rules can be loaded and executed
    matcher = RegexpMatcher()
    _ = matcher.process([sentence])
