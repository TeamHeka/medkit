import pytest
import spacy
from spacy.tokens import Doc, Span as SpacySpan

from medkit.core import Attribute
from medkit.core.text import Span, Entity, Segment, TextDocument, EntityNormAttribute
from medkit.text.spacy import spacy_utils


@pytest.fixture(scope="module")
def nlp_spacy():
    return spacy.blank("en")


TEXT = (
    "The patient's father was prescribed Lisinopril because he was suffering from"
    " severe hypertension.\nThe patient is taking Levothyroxine"
)


def _get_doc():
    medkit_doc = TextDocument(text=TEXT)

    # entities
    ent_1 = Entity(
        label="medication", spans=[Span(36, 46)], text="Lisinopril", attrs=[]
    )
    ent_2_attr = Attribute(label="severity", value="high")
    ent_2 = Entity(
        label="disease", spans=[Span(84, 96)], text="hypertension", attrs=[ent_2_attr]
    )
    ent_3 = Entity(
        label="medication", spans=[Span(120, 133)], text="Levothyroxine", attrs=[]
    )

    # segments
    seg_1_attr = Attribute(label="family", value=True)
    seg_1 = Segment(
        label="PEOPLE",
        spans=[Span(0, 20)],
        text="The patient's father",
        attrs=[seg_1_attr],
    )

    seg_2_attr = Attribute(label="family", value=False)
    seg_2 = Segment(
        label="PEOPLE", spans=[Span(98, 109)], text="The patient", attrs=[seg_2_attr]
    )

    for ann in [ent_1, ent_2, ent_3, seg_1, seg_2]:
        medkit_doc.anns.add(ann)

    return medkit_doc


def _assert_spacy_doc(doc, raw_annotation):
    assert isinstance(doc, Doc)
    assert Doc.has_extension("medkit_id")
    assert doc._.get("medkit_id") == raw_annotation.uid


# test medkit doc to spacy doc
def test_medkit_to_spacy_doc_without_anns(nlp_spacy):
    medkit_doc = _get_doc()
    raw_segment = medkit_doc.raw_segment

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=[],
        attrs=[],
        include_medkit_info=True,
    )
    # spacy doc was created and has the same ID as raw_ann
    _assert_spacy_doc(spacy_doc, raw_segment)
    assert spacy_doc.text == medkit_doc.text
    # no ents were transfered
    assert spacy_doc.ents == ()

    # test without medkit info
    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=[],
        attrs=[],
        include_medkit_info=False,
    )
    assert spacy_doc.text == medkit_doc.text
    assert spacy_doc._.get("medkit_id") is None


def test_medkit_to_spacy_doc_selected_ents_list(nlp_spacy):
    medkit_doc = _get_doc()
    raw_segment = medkit_doc.raw_segment

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=["medication", "disease"],
        attrs=[],
        include_medkit_info=True,
    )
    # spacy doc was created and has the same ID as raw_ann
    _assert_spacy_doc(spacy_doc, raw_segment)
    assert spacy_doc.text == medkit_doc.text
    # ents were transfer, 2 for medication, 1 for disease
    assert len(spacy_doc.ents) == 3

    ents = medkit_doc.anns.get_entities()
    # guarantee the same order to compare
    doc_ents = sorted(
        spacy_doc.ents, key=lambda ent_spacy: ent_spacy._.get("medkit_id")
    )
    ents = sorted(ents, key=lambda sp: sp.uid)

    # each entity created has the same uid and label as its entity of origin
    for ent_spacy, ent_medkit in zip(doc_ents, ents):
        assert ent_spacy._.get("medkit_id") == ent_medkit.uid
        assert ent_spacy.label_ == ent_medkit.label

    # check disease spacy span
    disease_spacy_span = next(e for e in doc_ents if e.label_ == "disease")
    assert (disease_spacy_span.start_char, disease_spacy_span.end_char) == (84, 96)

    # test warning for labels
    with pytest.warns(UserWarning, match=r"No medkit annotations"):
        spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
            nlp=nlp_spacy,
            medkit_doc=medkit_doc,
            labels_anns=["person"],
            attrs=[],
            include_medkit_info=True,
        )


def test_medkit_to_spacy_doc_all_anns(nlp_spacy):
    # testing getting a spacy doc with all annotations from a medkit doc
    medkit_doc = _get_doc()
    raw_segment = medkit_doc.raw_segment

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=None,
        attrs=[],
        include_medkit_info=True,
    )
    _assert_spacy_doc(spacy_doc, raw_segment)
    assert spacy_doc.text == medkit_doc.text
    assert len(spacy_doc.ents) == 3
    assert len(spacy_doc.spans) == 1
    assert len(spacy_doc.spans["PEOPLE"]) == 2


def test_medkit_to_spacy_doc_all_anns_family_attr(nlp_spacy):
    medkit_doc = _get_doc()
    raw_segment = medkit_doc.raw_segment
    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=None,
        attrs=["family"],
        include_medkit_info=True,
    )
    _assert_spacy_doc(spacy_doc, raw_segment)
    assert spacy_doc.text == medkit_doc.text
    assert len(spacy_doc.ents) == 3
    assert len(spacy_doc.spans) == 1
    assert len(spacy_doc.spans["PEOPLE"]) == 2

    # testing attrs in spans
    assert SpacySpan.has_extension("family")
    assert isinstance(spacy_doc.spans["PEOPLE"][0]._.get("family"), bool)
    # entity is a span but family should be NONE
    assert spacy_doc.ents[0]._.get("family") is None


def test_medkit_segments_to_spacy_docs(nlp_spacy):
    # test medkit segments to spacy doc
    medkit_doc = _get_doc()
    segments = medkit_doc.anns.get(label="PEOPLE")

    for ann_source in segments:
        doc = spacy_utils.build_spacy_doc_from_medkit_segment(
            nlp=nlp_spacy, segment=ann_source, annotations=[], include_medkit_info=True
        )
        assert isinstance(doc, Doc)
        assert Doc.has_extension("medkit_id")
        assert doc._.get("medkit_id") == ann_source.uid
        assert doc.text == ann_source.text

    # testing when 'include_medkit_info' is False
    for ann_source in segments:
        doc = spacy_utils.build_spacy_doc_from_medkit_segment(
            nlp=nlp_spacy, segment=ann_source, annotations=[], include_medkit_info=False
        )
        assert isinstance(doc, Doc)
        assert doc._.get("medkit_id") is None
        assert doc.text == ann_source.text


def test_normalization_attr(nlp_spacy):
    """Conversion of normalization objects to strings"""

    text = "Le patient souffre d'asthme"
    doc = TextDocument(text=text)
    entity = Entity(label="maladie", text="asthme", spans=[Span(21, 27)])
    entity.attrs.add(
        EntityNormAttribute(kb_name="umls", kb_id="C0004096", kb_version="2021AB")
    )
    doc.anns.add(entity)

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy, medkit_doc=doc
    )
    assert spacy_doc.ents[0]._.get("NORMALIZATION") == "umls:C0004096"
