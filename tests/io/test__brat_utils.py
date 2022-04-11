import pathlib

import pytest

from medkit.io._brat_utils import (
    Entity,
    Attribute,
    Relation,
    _parse_entity,
    _parse_relation,
    _parse_attribute,
    parse_file,
)


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
    assert entity in doc.entities.values()
    relation = Relation(id="R1", type="treats", subj="T1", obj="T3")
    assert relation in doc.relations.values()
    attribute = Attribute(id="A1", type="negation", target="R1")
    assert attribute in doc.attributes.values()


def test_document_get_augmented_entities():
    test_file = pathlib.Path("tests/data/brat/2_augmented_entities.ann")
    doc = parse_file(test_file)
    augmented_entities = doc.get_augmented_entities()
    assert "T4" in augmented_entities.keys()
    entity = augmented_entities["T4"]
    assert entity.text == "entity1 entity2"
    assert entity.type == "And-Group"
    assert entity.span == ((30, 37), (120, 127))
    relation1 = Relation(id="R1", type="And", subj="T4", obj="T1")
    relation2 = Relation(id="R3", type="Or", subj="T5", obj="T4")
    assert relation1 in entity.relations_from_me
    assert relation2 in entity.relations_to_me
    attribute = Attribute(id="A1", type="attribute", target="T4")
    assert attribute in entity.attributes


def test_document_grouping():
    test_file = pathlib.Path("tests/data/brat/2_augmented_entities.ann")
    doc = parse_file(test_file, detect_groups=True)
    assert "T1" not in doc.groups.keys()
    # Test And-Group
    assert "T4" in doc.groups.keys()
    and_group = doc.groups["T4"]
    assert and_group.type == "And-Group"
    entity1 = Entity(id="T1", type="label1", span=((30, 37),), text="entity1")
    assert entity1 in and_group.items
    # Test Or-Group
    assert "T5" in doc.groups.keys()
    or_group = doc.groups["T5"]
    assert or_group.type == "Or-Group"
    entity3 = Entity(id="T3", type="label3", span=((140, 147),), text="entity3")
    assert entity3 in or_group.items
