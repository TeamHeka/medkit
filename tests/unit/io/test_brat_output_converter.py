from pathlib import Path
import pytest

from medkit.core import Attribute
from medkit.core.text import Entity, Relation, Segment, Span, TextDocument
from medkit.io._brat_utils import BratAttribute, BratEntity, convert_medkit_anns_to_brat
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


TEST_LABELS_ANNS = [
    (None, True, 4),  # 4 entities
    ([], True, 0),
    (["maladie"], True, 2),
    (None, False, 5),  # 4 entities + 1 segment
    ([], False, 0),
    (["maladie"], False, 2),
]


@pytest.mark.parametrize(
    "anns_labels,ignore_segments,expected_nb_brat_entities",
    TEST_LABELS_ANNS,
    ids=[
        "default_keep_segment",
        "no_annotations_keep_segment",
        "entity_by_label_keep_segment",
        "default_no_segment",
        "no_annotations_no_segment",
        "entity_by_label_no_segment",
    ],
)
def test_entity_conversion(
    anns_labels,
    ignore_segments,
    expected_nb_brat_entities,
):
    # create medkit_doc with 4 entities, 1 relation, 1 segment, 2 attrs
    medkit_doc = _get_medkit_doc()

    # define a brat output converter without attrs
    brat_converter = BratOutputConverter(
        anns_labels=anns_labels,
        ignore_segments=ignore_segments,
        create_config=False,
        attrs=[],
    )

    # only segments are important for this test
    segments, _, _ = brat_converter._get_anns_from_medkit_doc(medkit_doc)
    segments = sorted(segments, key=lambda x: x.id)
    brat_anns, _ = convert_medkit_anns_to_brat(segments, [], [])
    assert len(brat_anns) == expected_nb_brat_entities

    for brat_ann, segment in zip(brat_anns, segments):
        assert isinstance(brat_ann, BratEntity)
        assert brat_ann.type == segment.label
        assert brat_ann.start == segment.spans[0].start
        assert brat_ann.end == segment.spans[-1].end
        assert brat_ann.text == segment.text


TEST_ATTRS = [
    (None, [True, True, False]),
    ([], []),
    (["from_umls"], [False]),
]


@pytest.mark.parametrize(
    "attrs_to_convert,expected_is_from_entity",
    TEST_ATTRS,
    ids=[
        "all_attrs",
        "no_attrs",
        "attr_by_label",
    ],
)
def test_attrs_conversion(attrs_to_convert, expected_is_from_entity):
    # create medkit_doc with 4 entities, 1 relation, 1 segment, 2 attrs
    medkit_doc = _get_medkit_doc()

    # define a brat output converter all anns selected attrs
    brat_converter = BratOutputConverter(
        anns_labels=None,
        ignore_segments=True,
        create_config=False,
        attrs=attrs_to_convert,
    )

    segments, relations, attrs = brat_converter._get_anns_from_medkit_doc(medkit_doc)
    segments = sorted(segments, key=lambda x: x.id)
    brat_anns, _ = convert_medkit_anns_to_brat(segments, relations, attrs)

    # only check brat attributes
    brat_attrs = [ann for ann in brat_anns if isinstance(ann, BratAttribute)]
    assert len(brat_attrs) == len(expected_is_from_entity)
    assert [attr.is_from_entity for attr in brat_attrs] == expected_is_from_entity


EXPECTED_ANN = """T1\tmaladie 24 42\tdouleur abdominale
T2\tgrade 46 53\tgrade 4
A1\tnormalized T2 True
T3\tmaladie 58 76\tdouleur abdominale
T4\tlevel 81 87\tsévère
A2\tnormalized T4 False
T5\tdiagnosis 0 42;81 87\tLe patient présente une douleur abdominale sévère
R1\trelated Arg1:T1 Arg2:T3
A3\tfrom_umls R1
"""


@pytest.mark.parametrize(
    "create_config",
    [False, True],
    ids=[
        "with_config",
        "no_config",
    ],
)
def test_convert(tmp_path: Path, create_config):
    # create medkit_doc with 4 entities, 1 relation, 1 segment, 2 attrs
    medkit_doc = _get_medkit_doc()
    # sort for testing
    medkit_doc.annotation_ids = sorted(medkit_doc.annotation_ids)

    # define a brat output converter all anns selected attrs
    brat_converter = BratOutputConverter(
        anns_labels=None,
        ignore_segments=False,
        create_config=create_config,
        attrs=None,
    )
    output_path = tmp_path / "output"
    expected_txt_path = output_path / f"{medkit_doc.id}.txt"
    expected_ann_path = output_path / f"{medkit_doc.id}.ann"
    expected_conf_path = output_path / "annotation.conf"
    brat_converter.convert([medkit_doc], output_path)

    assert output_path.exists()
    assert expected_txt_path.exists()
    assert expected_ann_path.exists()
    assert expected_txt_path.read_text() == medkit_doc.text
    assert expected_ann_path.read_text() == EXPECTED_ANN
    if create_config:
        assert expected_conf_path.exists()
    else:
        assert not expected_conf_path.exists()
