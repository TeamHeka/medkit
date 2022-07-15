from pathlib import Path
import pytest

from medkit.core import Attribute
from medkit.core.text import Entity, Relation, Segment, Span, TextDocument
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
    segments, relations = brat_converter._get_anns_from_medkit_doc(medkit_doc)
    _, config_file = brat_converter._convert_medkit_anns_to_brat(segments, relations)

    assert config_file.entity_types == ["grade", "level", "maladie"]
    assert "normalized" in config_file.attr_entity_values.keys()
    assert "from_umls" in config_file.attr_relation_values.keys()
    assert "related" in config_file.rel_types_arg_1.keys()
    assert "related" in config_file.rel_types_arg_2.keys()

    # already sorted
    assert config_file.to_str() == EXPECTED_CONFIG
