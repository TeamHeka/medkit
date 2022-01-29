import pathlib

import pytest

from medkit.io.brat import Entity, Attribute, Relation
from medkit.io.brat import _parse_entity, _parse_relation, _parse_attribute, parse_file


def test__parse_entity():
    brat_entity = "T1	medication 36  46	Lisinopril\t"
    entity_id, entity_content = brat_entity.split("\t", maxsplit=1)
    entity = _parse_entity(entity_id, entity_content)
    assert entity.id == "T1"
    assert entity.type == "medication"
    assert entity.span == ((36, 46),)
    assert entity.text == "Lisinopril"


def test__parse__entity_discontinued_span():
    brat_entity = "T6	vitamin 251 260;263 264	vitamins D"
    entity_id, entity_content = brat_entity.split("\t", maxsplit=1)
    entity = _parse_entity(entity_id, entity_content)
    assert entity.span == ((251, 260), (263, 264))


def test__parse_entity_error():
    brat_entity = "T1	medication 36 46 Lisinopril"
    entity_id, entity_content = brat_entity.split("\t", maxsplit=1)
    with pytest.raises(ValueError):
        _parse_entity(entity_id, entity_content)


def test__parse_relation():
    brat_relation = "R1	treats Arg1:T1 Arg2:T3"
    relation_id, relation_content = brat_relation.split("\t", maxsplit=1)
    relation = _parse_relation(relation_id, relation_content)
    assert relation.id == "R1"
    assert relation.type == "treats"
    assert relation.subj == "T1"
    assert relation.obj == "T3"


def test__parse_relation_error():
    brat_relation = "R1	treats  Arg1:T1\t"
    relation_id, relation_content = brat_relation.split("\t", maxsplit=1)
    with pytest.raises(ValueError):
        _parse_relation(relation_id, relation_content)


def test__parse_attribute():
    brat_attribute = "A3	 antecedent T4"
    attribute_id, attribute_content = brat_attribute.split("\t", maxsplit=1)
    attribute = _parse_attribute(attribute_id, attribute_content)
    assert attribute.id == "A3"
    assert attribute.type == "antecedent"
    assert attribute.target == "T4"


def test__parse_attribute_value():
    brat_attribute = "A2	severity R2  normal "
    attribute_id, attribute_content = brat_attribute.split("\t", maxsplit=1)
    attribute = _parse_attribute(attribute_id, attribute_content)
    assert attribute.value == "normal"


def test__parse_attribute_error():
    brat_attribute = "A2	severity "
    attribute_id, attribute_content = brat_attribute.split("\t", maxsplit=1)
    with pytest.raises(ValueError):
        _parse_attribute(attribute_id, attribute_content)


def test_parse_file():
    test_file = pathlib.Path("tests/data/brat/1_example.ann")
    doc = parse_file(str(test_file))
    entity = Entity(id="T1", type="medication", span=((36, 46),), text="Lisinopril")
    assert entity in doc.entities
    relation = Relation(id="R1", type="treats", subj="T1", obj="T3")
    assert relation in doc.relations
    attribute = Attribute(id="A1", type="negation", target="R1")
    assert attribute in doc.attributes
