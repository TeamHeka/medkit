import pathlib

import pytest
from medkit.core.annotation import Attribute
from medkit.core.text.annotation import Entity, Relation, Segment
from medkit.core.text.span import Span

from medkit.io._brat_utils import (
    BratEntity,
    BratAttribute,
    BratRelation,
    BratRelationAugmented,
    AttributeConf,
    RelationConf,
    _parse_entity,
    _parse_relation,
    _parse_attribute,
    parse_file,
    _convert_attribute_to_brat,
    _convert_segment_to_brat,
    _convert_relation_to_brat,
    get_configuration_from_anns,
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
    entity = BratEntity(id="T1", type="medication", span=((36, 46),), text="Lisinopril")
    assert entity in doc.entities.values()
    relation = BratRelation(id="R1", type="treats", subj="T1", obj="T3")
    assert relation in doc.relations.values()
    attribute = BratAttribute(id="A1", type="negation", target="R1")
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
    relation1 = BratRelation(id="R1", type="And", subj="T4", obj="T1")
    relation2 = BratRelation(id="R3", type="Or", subj="T5", obj="T4")
    assert relation1 in entity.relations_from_me
    assert relation2 in entity.relations_to_me
    attribute = BratAttribute(id="A1", type="attribute", target="T4")
    assert attribute in entity.attributes


def test_document_grouping():
    test_file = pathlib.Path("tests/data/brat/2_augmented_entities.ann")
    doc = parse_file(test_file, detect_groups=True)
    assert "T1" not in doc.groups.keys()
    # Test And-Group
    assert "T4" in doc.groups.keys()
    and_group = doc.groups["T4"]
    assert and_group.type == "And-Group"
    entity1 = BratEntity(id="T1", type="label1", span=((30, 37),), text="entity1")
    assert entity1 in and_group.items
    # Test Or-Group
    assert "T5" in doc.groups.keys()
    or_group = doc.groups["T5"]
    assert or_group.type == "Or-Group"
    entity3 = BratEntity(id="T3", type="label3", span=((140, 147),), text="entity3")
    assert entity3 in or_group.items


def test__convert_segment_to_brat():
    segment_medkit = Segment(
        label="label_segment", spans=[Span(0, 5)], text="segment_text"
    )
    with pytest.raises(AssertionError):
        _convert_segment_to_brat(
            segment=segment_medkit,
            nb_segment=0,
        )

    brat_entity = _convert_segment_to_brat(
        segment=segment_medkit,
        nb_segment=1,
    )
    assert isinstance(brat_entity, BratEntity)
    assert brat_entity.id == "T1"
    assert brat_entity.type == "label_segment"
    assert brat_entity.span == ((0, 5),)
    assert brat_entity.text == "segment_text"


def test__convert_attribute_to_brat():
    with pytest.raises(AssertionError):
        _convert_attribute_to_brat(
            Attribute(label="label_attr", value=None),
            nb_attribute=0,
            target_brat_id="T1",
            is_from_entity=False,
        )

    brat_attribute = _convert_attribute_to_brat(
        Attribute(label="label_attr", value=None),
        nb_attribute=1,
        target_brat_id="T1",
        is_from_entity=False,
    )
    assert isinstance(brat_attribute, BratAttribute)
    assert brat_attribute.id == "A1"
    assert brat_attribute.type == "label_attr"
    assert brat_attribute.value is None
    assert brat_attribute.target == "T1"


def test__convert_relation():
    ent_1 = Entity(
        entity_id="id_1", label="ent_suj", spans=[Span(0, 10)], text="ent_1_text"
    )
    ent_2 = Entity(
        entity_id="id_2", label="ent_suj", spans=[Span(0, 10)], text="ent_1_text"
    )
    relation = Relation(label="rel1", source_id=ent_1.id, target_id=ent_2.id)

    # create entities brat and save them in a dict
    anns_by_medkit_id = dict()
    anns_by_medkit_id[ent_1.id] = _convert_segment_to_brat(ent_1, nb_segment=1)
    anns_by_medkit_id[ent_2.id] = _convert_segment_to_brat(ent_2, nb_segment=2)

    brat_relation = _convert_relation_to_brat(
        relation=relation, nb_relation=1, brat_anns_by_segment_id=anns_by_medkit_id
    )
    assert isinstance(brat_relation, BratRelation)
    assert isinstance(brat_relation, BratRelationAugmented)
    assert brat_relation.id == "R1"
    assert brat_relation.subj == anns_by_medkit_id[ent_1.id]
    assert brat_relation.obj == anns_by_medkit_id[ent_2.id]
    assert brat_relation.type == "rel1"
    assert str(brat_relation) == "R1\trel1 Arg1:T1 Arg2:T2\n"


def test_attribute_conf_file():
    # generate a configuration line for brat attributes
    # a brat entity has an attribute 'severity' value 'normal')
    attr_conf = AttributeConf(from_entity=True, type="severity", values=set(["normal"]))
    assert "normal" in attr_conf.values
    # another brat entity has an attribute 'severity' value 'low')
    # we update the set of values of this attribute configuration
    attr_conf.update(["low"])
    # sorted to test the str representation
    attr_conf.values = sorted(attr_conf.values)
    assert attr_conf.values == ["low", "normal"]
    assert str(attr_conf) == "severity\tArg:<ENTITY>, Value:low|normal"


def test_relation_conf_file():
    # generate a configuration line for brat relations
    # a brat relation has subj type 'medicament_1' and obj type 'disease'
    relation_conf = RelationConf(
        type="treats", args1=set(["medicament_1"]), args2=set(["disease"])
    )
    assert relation_conf.type == "treats"
    assert "medicament_1" in relation_conf.args1
    assert "disease" in relation_conf.args2
    # the same relation exists between subj type 'medicament_2' and obj type 'disease'
    # we update the set of args1 of this relation configuration
    relation_conf.update(args1=["medicament_2"], args2=["disease"])
    # sorted to test the str representation
    relation_conf.args1 = sorted(relation_conf.args1)
    relation_conf.args2 = sorted(relation_conf.args2)
    assert relation_conf.args1 == ["medicament_1", "medicament_2"]
    assert relation_conf.args2 == ["disease"]
    assert str(relation_conf) == "treats\tArg1:medicament_1|medicament_2, Arg2:disease"


EXPECTED_CONFIG = """#Text-based definitions of entity types, relation types
#and attributes. This file was generated using medkit
#from the HeKa project
[entities]

disease
medicament
[relations]

# This line enables entity overlapping
<OVERLAP>\tArg1:<ENTITY>, Arg2:<ENTITY>, <OVL-TYPE>:<ANY>
treats\tArg1:medicament, Arg2:disease
related\tArg1:medicament, Arg2:medicament
[attributes]

code\tArg:<ENTITY>, Value:1234|5463
negation\tArg:<RELATION>
[events]\n\n"""


def test_annotation_conf_file():
    # generate an annotation configuration for brat anns
    ent_1 = BratEntity("T1", "medicament", (0, 5), "brand")
    attr_1 = BratAttribute("A1", "code", "T1", "1234", is_from_entity=True)
    ent_2 = BratEntity("T2", "disease", (0, 7), "maladie")
    attr_2 = BratAttribute("A2", "code", "T3", "5463", is_from_entity=True)
    ent_3 = BratEntity("T3", "medicament", (0, 7), "brand_2")
    rel_1 = BratRelationAugmented("R1", "treats", ent_1, ent_2)
    rel_2 = BratRelationAugmented("R2", "related", ent_1, ent_3)
    attr_3 = BratAttribute("A3", "negation", "R1", None, is_from_entity=False)

    brat_anns = [ent_1, ent_2, ent_3, attr_1, attr_2, attr_3, rel_1, rel_2]
    config_file = get_configuration_from_anns(brat_anns)

    assert "code" in config_file.attribute_types.keys()
    assert "negation" in config_file.attribute_types.keys()
    assert "treats" in config_file.relation_types.keys()
    assert "related" in config_file.relation_types.keys()

    # to test we sort sets, this converts sets to list
    config_file.entity_types = sorted(config_file.entity_types)
    for key in config_file.attribute_types.keys():
        config_file.attribute_types[key].values = sorted(
            config_file.attribute_types[key].values
        )

    assert str(config_file) == EXPECTED_CONFIG
