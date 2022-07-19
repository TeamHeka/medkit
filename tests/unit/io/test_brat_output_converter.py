from pathlib import Path
import pytest

from medkit.core import Attribute
from medkit.core.text import Entity, Relation, Segment, Span, TextDocument
from medkit.io._brat_utils import (
    BratAttribute,
    BratEntity,
    BratRelation,
    BratAnnConfiguration,
)
from medkit.io.brat import BratOutputConverter


def _get_medkit_doc():
    text = (
        "Le patient présente une douleur abdominale de grade 4, la douleur abdominale"
        " est sévère."
    )
    doc = TextDocument(doc_id="doc_brat", text=text)
    medkit_anns = [
        Entity(
            spans=[Span(24, 42)],
            label="maladie",
            text="douleur abdominale",
            entity_id="e1",
        ),
        Entity(
            spans=[Span(46, 53)],
            label="grade",
            text="grade 4",
            entity_id="e2",
            attrs=[Attribute("normalized", True)],
        ),
        Entity(
            spans=[Span(58, 76)],
            label="maladie",
            text="douleur abdominale",
            entity_id="e3",
        ),
        Entity(
            spans=[Span(81, 87)],
            label="level",
            text="sévère",
            entity_id="e4",
            attrs=[Attribute("normalized", False)],
        ),
        Relation(
            label="related",
            source_id="e1",
            target_id="e3",
            attrs=[Attribute("from_umls")],
            rel_id="r1",
        ),
        Segment(
            label="diagnosis",
            spans=[Span(0, 42), Span(81, 87)],
            text="Le patient présente une douleur abdominale sévère",
            ann_id="s1",
        ),
    ]
    for ann in medkit_anns:
        doc.add_annotation(ann)

    return doc


TEST_DATA = [
    (
        None,
        None,
        False,
        False,
        """T1\tmaladie 24 42\tdouleur abdominale
T2\tgrade 46 53\tgrade 4
A1\tnormalized T2
T3\tmaladie 58 76\tdouleur abdominale
T4\tlevel 81 87\tsévère
T5\tdiagnosis 0 42;81 87\tLe patient présente une douleur abdominale sévère
R1\trelated Arg1:T1 Arg2:T3
A2\tfrom_umls R1
""",
    ),
    ([], [], False, False, ""),
    (
        ["maladie", "related"],
        ["from_umls"],
        False,
        False,
        """T1\tmaladie 24 42\tdouleur abdominale
T2\tmaladie 58 76\tdouleur abdominale
R1\trelated Arg1:T1 Arg2:T2
A1\tfrom_umls R1
""",
    ),
    (
        None,
        None,
        True,
        True,
        """T1\tmaladie 24 42\tdouleur abdominale
T2\tgrade 46 53\tgrade 4
A1\tnormalized T2
T3\tmaladie 58 76\tdouleur abdominale
T4\tlevel 81 87\tsévère
R1\trelated Arg1:T1 Arg2:T3
A2\tfrom_umls R1
""",
    ),
    ([], [], True, True, ""),
    (
        ["maladie", "related"],
        ["from_umls"],
        True,
        True,
        """T1\tmaladie 24 42\tdouleur abdominale
T2\tmaladie 58 76\tdouleur abdominale
R1\trelated Arg1:T1 Arg2:T2
A1\tfrom_umls R1
""",
    ),
]


@pytest.mark.parametrize(
    "ann_labels,attrs,ignore_segments,create_config,expected_ann",
    TEST_DATA,
    ids=[
        "all_anns_all_attrs",
        "no_anns_no_attrs",
        "list_anns_list_attrs",
        "all_anns_all_attrs_no_segment",
        "no_anns_no_attrs_no_segment",
        "list_anns_list_attrs_no_segment",
    ],
)
def test_save(
    tmp_path: Path, ann_labels, attrs, ignore_segments, create_config, expected_ann
):
    # create medkit_doc with 4 entities, 1 relation, 1 segment, 2 attrs
    medkit_doc = _get_medkit_doc()
    medkit_doc.annotation_ids = sorted(medkit_doc.annotation_ids)
    output_path = tmp_path / "output"
    expected_txt_path = output_path / f"{medkit_doc.id}.txt"
    expected_ann_path = output_path / f"{medkit_doc.id}.ann"
    expected_conf_path = output_path / "annotation.conf"

    # define a brat output converter all anns all attrs
    brat_converter = BratOutputConverter(
        anns_labels=ann_labels,
        ignore_segments=ignore_segments,
        create_config=create_config,
        attrs=attrs,
    )

    brat_converter.save([medkit_doc], output_path)

    assert output_path.exists()
    assert expected_txt_path.exists()
    assert expected_ann_path.exists()
    assert expected_txt_path.read_text() == medkit_doc.text
    assert expected_ann_path.read_text() == expected_ann
    if create_config:
        assert expected_conf_path.exists()
    else:
        assert not expected_conf_path.exists()


EXPECTED_CONFIG = """#Text-based definitions of entity types, relation types
#and attributes. This file was generated using medkit
#from the HeKa project
[entities]

grade
level
maladie
[relations]

# This line enables entity overlapping
<OVERLAP>\tArg1:<ENTITY>, Arg2:<ENTITY>, <OVL-TYPE>:<ANY>
related\tArg1:maladie, Arg2:maladie
[attributes]

normalized\tArg:<ENTITY>
from_umls\tArg:<RELATION>
[events]\n\n"""


def test_annotation_conf_file():
    # test to check configuration file
    # create medkit_doc with 4 entities, 1 relation, 1 segment, 2 attrs
    medkit_doc = _get_medkit_doc()

    brat_converter = BratOutputConverter(
        anns_labels=None,
        ignore_segments=True,
        create_config=True,
        attrs=None,
    )
    config_file = BratAnnConfiguration()
    segments, relations = brat_converter._get_anns_from_medkit_doc(medkit_doc)
    _, config_file = brat_converter._convert_medkit_anns_to_brat(
        segments, relations, config_file
    )

    assert config_file.entity_types == ["grade", "level", "maladie"]
    assert "normalized" in config_file.attr_entity_values.keys()
    assert "from_umls" in config_file.attr_relation_values.keys()
    assert "related" in config_file.rel_types_arg_1.keys()
    assert "related" in config_file.rel_types_arg_2.keys()

    # already sorted
    assert config_file.to_str() == EXPECTED_CONFIG


def test__convert_segment_to_brat():
    segment_medkit = Segment(
        label="label_segment", spans=[Span(0, 5)], text="segment_text"
    )
    with pytest.raises(AssertionError):
        BratOutputConverter._convert_segment_to_brat(
            segment=segment_medkit,
            nb_segment=0,
        )

    brat_entity = BratOutputConverter._convert_segment_to_brat(
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
        BratOutputConverter._convert_attribute_to_brat(
            label="label_attr",
            value=None,
            nb_attribute=0,
            target_brat_id="T1",
            is_from_entity=False,
        )

    brat_attribute, _ = BratOutputConverter._convert_attribute_to_brat(
        label="label_attr",
        value=None,
        nb_attribute=1,
        target_brat_id="T1",
        is_from_entity=False,
    )
    assert isinstance(brat_attribute, BratAttribute)
    assert brat_attribute.id == "A1"
    assert brat_attribute.type == "label_attr"
    assert brat_attribute.value == ""
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
    anns_by_medkit_id[ent_1.id] = BratOutputConverter._convert_segment_to_brat(
        ent_1, nb_segment=1
    )
    anns_by_medkit_id[ent_2.id] = BratOutputConverter._convert_segment_to_brat(
        ent_2, nb_segment=2
    )

    brat_relation, _ = BratOutputConverter._convert_relation_to_brat(
        relation=relation, nb_relation=1, brat_anns_by_segment_id=anns_by_medkit_id
    )
    assert isinstance(brat_relation, BratRelation)
    assert brat_relation.id == "R1"
    assert brat_relation.subj == anns_by_medkit_id[ent_1.id].id
    assert brat_relation.obj == anns_by_medkit_id[ent_2.id].id
    assert brat_relation.type == "rel1"
    assert brat_relation.to_str() == "R1\trel1 Arg1:T1 Arg2:T2\n"
