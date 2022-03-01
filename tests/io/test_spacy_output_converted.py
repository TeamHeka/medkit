import pytest
import spacy.cli
from medkit.core.text import Span as MedkitSpan
from medkit.core.text.annotation import Attribute, Entity, Segment
from medkit.core.text.document import TextDocument
from medkit.io.spacy import SpacyOutputConvert
from spacy.tokens import Doc


@pytest.fixture(scope="module")
def nlp_spacy():
    # download spacy models to test sents transfer
    if not spacy.util.is_package("en_core_web_sm"):
        spacy.cli.download("en_core_web_sm")
    return spacy.load("en_core_web_sm")


TEXT = (
    "The patient's father was prescribed Lisinopril because he was suffering from"
    " severe hypertension.\nThe patient is taking Levothyroxine"
)
ENTITIES = [
    ("medication", (36, 46), "Lisinopril", []),
    (
        "disease",
        (84, 96),
        "hypertension",
        [Attribute(label="severity", value="high")],
    ),
    ("medication", (120, 133), "Levothyroxine", []),
]

SEGMENTS = [
    (
        "PEOPLE",
        (0, 20),
        "The patient's father",
        [Attribute(label="family", value=True)],
    ),
    (
        "PEOPLE",
        (98, 109),
        "The patient",
        [Attribute(label="family", value=False)],
    ),
]


def _get_doc():
    medkit_doc = TextDocument(text=TEXT)
    for ent in ENTITIES:
        medkit_doc.add_annotation(_create_entity(*ent))

    for seg in SEGMENTS:
        medkit_doc.add_annotation(_create_segment(*seg))

    return medkit_doc


def _create_entity(label, span, text, attrs):
    return Entity(
        label=label,
        spans=[MedkitSpan(span[0], span[1])],
        text=text,
        attrs=attrs,
    )


def _create_segment(label, span, text, attrs):
    return Segment(
        label=label,
        spans=[MedkitSpan(span[0], span[1])],
        text=text,
        attrs=attrs,
    )


def _asssert_spacy_doc(doc, raw_annotation):
    assert isinstance(doc, Doc)
    assert doc.has_extension("medkit_id")
    assert doc._.get("medkit_id") == raw_annotation.id
    assert doc.has_extension("medkit_spans")
    assert doc._.get("medkit_spans") == raw_annotation.spans


TEST_ENTS_TO_SPACY = [
    (None, 3, ["medication", "disease"]),
    ([], 0, []),
    (["medication"], 2, ["medication"]),
]


@pytest.mark.parametrize(
    "labels_ents_to_transfer,expected_nb_ents,expected_label_ents",
    TEST_ENTS_TO_SPACY,
    ids=["all_ents", "no_annotations", "entity_by_label"],
)
def test_output_converter_entity_transfer(
    nlp_spacy, labels_ents_to_transfer, expected_nb_ents, expected_label_ents
):
    # get medkit document to test
    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    # testing output converter
    spacy_output_converter = SpacyOutputConvert(
        nlp_spacy,
        apply_nlp_spacy=False,
        labels_to_transfer=labels_ents_to_transfer,
        attrs_to_transfer=[],
    )
    spacy_docs = spacy_output_converter.convert([medkit_doc])
    # spacy doc was created and has the same ID as raw_ann
    assert len(spacy_docs) == 1
    spacy_doc = spacy_docs[0]

    _asssert_spacy_doc(spacy_doc, raw_annotation)

    assert len(spacy_doc.ents) == expected_nb_ents
    assert not spacy_doc.has_annotation("TAG")

    ents = [
        ent
        for label in expected_label_ents
        for ent in medkit_doc.get_annotations_by_label(label)
    ]

    # guarantee the same order to compare
    doc_ents = sorted(spacy_doc.ents, key=lambda sp: sp.label)
    ents = sorted(ents, key=lambda sp: sp.label)

    # each entity created has the same id as its entity of origin
    assert all(
        ent_spacy._.get("medkit_id") == ent_medkit.id
        for ent_spacy, ent_medkit in zip(doc_ents, ents)
    )

    # each entity created has the same span as its entity of origin
    assert all(
        ent_spacy._.get("medkit_spans") == ent_medkit.spans
        for ent_spacy, ent_medkit in zip(doc_ents, ents)
    )


def _span_spacy_by_medkit_id(medkit_id, spans):
    return [sp for sp in spans if sp._.get("medkit_id") == medkit_id]


def test_output_converter_attr_transfer(nlp_spacy):

    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    # testing output converter all attrs
    spacy_output_converter_1 = SpacyOutputConvert(
        nlp_spacy,
        apply_nlp_spacy=False,
        labels_to_transfer=None,
        attrs_to_transfer=None,
    )

    # testing output converter no attrs
    spacy_output_converter_2 = SpacyOutputConvert(
        nlp_spacy,
        apply_nlp_spacy=False,
        labels_to_transfer=None,
        attrs_to_transfer=[],
    )
    # testing output converter only family
    spacy_output_converter_3 = SpacyOutputConvert(
        nlp_spacy,
        apply_nlp_spacy=False,
        labels_to_transfer=None,
        attrs_to_transfer=["family"],
    )

    spacy_docs = [
        spacy_output_converter_1.convert([medkit_doc])[0],
        spacy_output_converter_2.convert([medkit_doc])[0],
        spacy_output_converter_3.convert([medkit_doc])[0],
    ]
    # spacy doc was created and has the same ID as raw_ann
    for spacy_doc in spacy_docs:
        _asssert_spacy_doc(spacy_doc, raw_annotation)
        assert spacy_doc.text == medkit_doc.text
        assert len(spacy_doc.ents) == 3
        assert len(spacy_doc.spans) == 1
        assert len(spacy_doc.spans["PEOPLE"]) == 2

    entity_desease = medkit_doc.get_annotations_by_label("disease")[0]
    segment_people = medkit_doc.get_annotations_by_label("PEOPLE")[0]

    for i, spacy_doc in enumerate(spacy_docs):
        ent_desease = _span_spacy_by_medkit_id(entity_desease.id, spacy_doc.ents)[0]
        span_people = _span_spacy_by_medkit_id(
            segment_people.id, spacy_doc.spans["PEOPLE"]
        )[0]

        assert span_people.has_extension("family")
        assert span_people.has_extension("severity")
        assert span_people._.get("severity") is None
        assert ent_desease._.get("family") is None
        if i == 0:
            # all attrs were transferred, so, values are no None
            assert span_people._.get("family")
            assert span_people._.get("family_") is not None
            assert ent_desease._.get("severity") == "high"
        elif i == 1:
            # no attrs were transferred, so, values are None
            assert span_people._.get("family") is None
            assert span_people._.get("family_") is None
            assert ent_desease._.get("severity") is None
        else:
            # only family was transferred, so, value is True
            assert span_people._.get("family")
            assert span_people._.get("family_") is not None
            assert ent_desease._.get("severity") is None
