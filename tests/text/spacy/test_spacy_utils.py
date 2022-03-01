import pytest
import spacy.cli
from medkit.core.text import Span as MedkitSpan
from medkit.core.text.annotation import Attribute, Entity, Segment
from medkit.core.text.document import TextDocument
from medkit.text.spacy import spacy_utils
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


# test medkit doc to spacy doc
def test_medkit_to_spacy_doc_without_anns(nlp_spacy):
    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit(
        nlp_spacy, raw_annotation, labels_to_transfer=[], attrs_to_transfer=[]
    )
    # spacy doc was created and has the same ID as raw_ann
    _asssert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    # no ents were transfered
    assert spacy_doc.ents == ()

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit(nlp_spacy, raw_annotation)

    # spacy doc was created and has the same ID as raw_ann
    _asssert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    # no ents were transfered
    assert spacy_doc.ents == ()

    with pytest.raises(
        AssertionError, match="'nlp' should be a Language instance from Spacy"
    ):
        spacy_doc = spacy_utils.build_spacy_doc_from_medkit([], raw_annotation)


def test_medkit_to_spacy_doc_selected_ents_list(nlp_spacy):
    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit(
        nlp_spacy,
        raw_annotation,
        medkit_doc.get_annotations(),
        labels_to_transfer=["medication", "disease"],
        attrs_to_transfer=[],
    )
    # spacy doc was created and has the same ID as raw_ann
    _asssert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    # ents were transfer, 2 for medication, 1 for disease
    assert len(spacy_doc.ents) == 3

    ents = [
        ent
        for label in ["medication", "disease"]
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

    assert all(
        (ent_spacy.start_char, ent_spacy.end_char)
        == spacy_utils._simplify_medkit_spans(ent_medkit.spans)
        for ent_spacy, ent_medkit in zip(doc_ents, ents)
    )


def test_medkit_to_spacy_doc_all_anns(nlp_spacy):
    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit(
        nlp_spacy,
        raw_annotation,
        medkit_doc.get_annotations(),
        labels_to_transfer=None,
        attrs_to_transfer=[],
    )
    _asssert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    assert len(spacy_doc.ents) == 3
    assert len(spacy_doc.spans) == 1
    assert len(spacy_doc.spans["PEOPLE"]) == 2


def test_medkit_to_spacy_doc_all_anns_family_attr(nlp_spacy):

    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]
    spacy_doc = spacy_utils.build_spacy_doc_from_medkit(
        nlp_spacy,
        raw_annotation,
        medkit_doc.get_annotations(),
        labels_to_transfer=None,
        attrs_to_transfer=["family"],
    )
    _asssert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    assert len(spacy_doc.ents) == 3
    assert len(spacy_doc.spans) == 1
    assert len(spacy_doc.spans["PEOPLE"]) == 2

    # testing attrs in spans
    assert spacy_doc.spans["PEOPLE"][0].has_extension("family")
    assert isinstance(spacy_doc.spans["PEOPLE"][0]._.get("family"), bool)
    # entity is a span but family should be NONE
    assert spacy_doc.ents[0]._.get("family") is None


# test medkit segments to spacy doc
def test_medkit_segments_to_spacy_docs(nlp_spacy):
    medkit_doc = _get_doc()
    segments = medkit_doc.get_annotations_by_label("PEOPLE")
    spacy_docs = [
        spacy_utils.build_spacy_doc_from_medkit(nlp_spacy, ann) for ann in segments
    ]
    assert len(spacy_docs) == 2
    [
        _asssert_spacy_doc(doc, ann_source)
        for doc, ann_source in zip(spacy_docs, segments)
    ]
