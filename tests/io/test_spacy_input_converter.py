import pytest

import spacy
from spacy.tokens import Span as SpacySpan

from medkit.core import ProvBuilder, Collection
from medkit.core.text import Entity, Span, TextDocument
from medkit.io.spacy import SpacyInputConverter
from medkit.text.spacy.spacy_utils import _define_attrs_extensions


@pytest.fixture(scope="module")
def nlp_spacy():
    # use an empty spacy nlp object
    return spacy.blank("en")


def _get_doc_spacy(nlp_spacy):
    """Spacy doc with entities and spans"""
    spacy_doc = nlp_spacy(
        "Marie Dupont started treatment at the central hospital in 2012"
    )
    # add entities in spacy doc
    ents = [spacy_doc.char_span(0, 12, "PERSON"), spacy_doc.char_span(58, 62, "DATE")]
    spacy_doc.ents = list(spacy_doc.ents) + ents
    # add span groups in spacy doc
    spacy_doc.spans["NOUN_CHUNKS"] = [spacy_doc[0:2], spacy_doc[3:4], spacy_doc[5:8]]
    spacy_doc.spans["SENTENCES"] = [spacy_doc[0:10]]
    return spacy_doc


TEST_ENTS_FROM_SPACY = [(None, 2), ([], 0), (["PERSON"], 1)]


@pytest.mark.parametrize(
    "labels_ents_to_transfer,expected_nb_ents",
    TEST_ENTS_FROM_SPACY,
    ids=["default", "no_annotations", "entity_by_label"],
)
def test_input_converter_entity_transfer(
    nlp_spacy,
    labels_ents_to_transfer,
    expected_nb_ents,
):

    # define a spacy input converter without spans or attributes
    spacy_converter = SpacyInputConverter(
        entities=labels_ents_to_transfer,
        span_groups=[],
        attrs=[],
    )
    # create a spacy doc containing 2 entities
    doc = _get_doc_spacy(nlp_spacy)

    # get a medkit doc from a spacy doc
    medkit_docs = spacy_converter.load([doc])

    assert isinstance(medkit_docs, Collection)
    assert len(medkit_docs.documents) == 1
    medkit_doc = medkit_docs.documents[0]

    assert isinstance(medkit_doc, TextDocument)
    # all entities should be included
    assert len(medkit_doc.entities.values()) == expected_nb_ents
    assert len(medkit_doc.get_annotations()) == expected_nb_ents

    ents = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.entities.values()
        for id in ids
    ]

    assert all(isinstance(ent, Entity) for ent in ents)
    # check entity
    if ents:
        entity_id_0 = medkit_doc.entities.get("PERSON", [])[0]
        entity_0 = medkit_doc.get_annotation_by_id(entity_id_0)
        assert entity_0.label == "PERSON"
        assert entity_0.text == "Marie Dupont"
        assert entity_0.spans == [Span(0, 12)]
        assert entity_0.attrs == []


TEST_ATTR_FROM_SPACY = [
    (None, [1, 2], [1, True]),
    ([], [0, 0], []),
    (["is_selected_ent"], [0, 1], [True]),
]


@pytest.mark.parametrize(
    "attrs_to_transfer,expected_nb_attrs,expected_values_attr_date",
    TEST_ATTR_FROM_SPACY,
    ids=["default", "no_attributes", "attr_by_label"],
)
def test_input_converter_attribute_transfer(
    nlp_spacy, attrs_to_transfer, expected_nb_attrs, expected_values_attr_date
):
    # define spacy extensions to test
    if not SpacySpan.has_extension("nb_tokens_in"):
        SpacySpan.set_extension("nb_tokens_in", default=None)

    if not SpacySpan.has_extension("is_selected_ent"):
        SpacySpan.set_extension("is_selected_ent", default=None)

    # define a spacy input converter to transfer all entities and selected attrs
    spacy_converter = SpacyInputConverter(
        entities=None,
        span_groups=[],
        attrs=attrs_to_transfer,
    )

    # create a spacy doc containing 2 entities
    doc = _get_doc_spacy(nlp_spacy)

    # simulates a component spacy that adds an attribute to all entities
    # add default argument
    for e in doc.ents:
        e._.set("nb_tokens_in", len([token for token in e]))

    # in the DATE entity it adds another attribute to test the transfer by attribute name
    for e in doc.ents:
        if e.label_ == "DATE":
            e._.set("is_selected_ent", True)

    # get a medkit doc from a spacy doc
    medkit_docs = spacy_converter.load([doc])

    assert isinstance(medkit_docs, Collection)
    assert len(medkit_docs.documents) == 1
    medkit_doc = medkit_docs.documents[0]

    assert isinstance(medkit_doc, TextDocument)
    assert len(medkit_doc.entities) == 2

    ents = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.entities.values()
        for id in ids
    ]
    # verify the number of attrs for each entity
    assert [len(ent.attrs) for ent in ents] == expected_nb_attrs

    # chech DATE entity
    date_entity = medkit_doc.get_annotations_by_label("DATE")[0]
    if date_entity.attrs:
        assert [a.value for a in date_entity.attrs] == expected_values_attr_date


def test_input_converter_medkit_attribute_transfer(nlp_spacy):
    # define an extension and a mock_attr_medkit
    if not SpacySpan.has_extension("nb_tokens_in"):
        SpacySpan.set_extension("nb_tokens_in", default=None)

    _define_attrs_extensions(["mock_attr_medkit"])

    # define a spacy input converter to transfer all entities,attrs and spans
    spacy_converter = SpacyInputConverter(
        entities=None,
        span_groups=None,
        attrs=None,
    )

    # create a spacy doc containing 3 entities
    doc = _get_doc_spacy(nlp_spacy)
    # add default argument
    for e in doc.ents:
        e._.set("nb_tokens_in", len([token for token in e]))
        e._.set("mock_attr_medkit", "medkit_put_this")
        e._.set("mock_attr_medkit_medkit_id", "12345")

    for sp in doc.spans["SENTENCES"]:
        sp._.set("mock_attr_medkit", "medkit_put_this_span")
        sp._.set("mock_attr_medkit_medkit_id", "123456")

    assert list(doc.spans["SENTENCES"])[0]._.get("nb_tokens_in") is None

    # get a medkit doc from a spacy doc

    medkit_docs = spacy_converter.load([doc])

    assert isinstance(medkit_docs, Collection)
    assert len(medkit_docs.documents) == 1
    medkit_doc = medkit_docs.documents[0]

    assert isinstance(medkit_doc, TextDocument)
    assert len(medkit_doc.entities.values()) == 2

    ents = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.entities.values()
        for id in ids
    ]
    # verify the number of attrs for each entity
    assert [len(ent.attrs) for ent in ents] == [2, 2]

    segments = medkit_doc.get_annotations_by_label("SENTENCES")
    # all sentences were transferred
    assert len(segments) == 1
    assert [len(seg.attrs) for seg in segments] == [1]

    noun_entity = medkit_doc.get_annotations_by_label("SENTENCES")[0]
    assert len(noun_entity.attrs) == 1
    assert noun_entity.attrs[0].label == "mock_attr_medkit"
    assert noun_entity.attrs[0].value == "medkit_put_this_span"


TEST_SEGMENTS_FROM_SPACY = [
    (None, ["SENTENCES", "NOUN_CHUNKS"], 4),
    ([], [], 0),
    (["NOUN_CHUNKS"], ["NOUN_CHUNKS"], 3),
]


@pytest.mark.parametrize(
    "name_spans_to_transfer,expected_labels_in_segments,expected_total_annotations",
    TEST_SEGMENTS_FROM_SPACY,
    ids=["default", "no_attributes", "attr_by_label"],
)
def test_input_converter_segments_transfer(
    nlp_spacy,
    name_spans_to_transfer,
    expected_labels_in_segments,
    expected_total_annotations,
):
    # in this test, we use sentences (doc.sents) and noun-chunks (doc.noun_chunks)
    # to create two span groups. Noun chunks are flat phrases that have a noun as their head.

    # define a spacy input converter to transfer selected spans, no entities nor attributes
    spacy_converter = SpacyInputConverter(
        entities=[],
        span_groups=name_spans_to_transfer,
        attrs=[],
    )

    # create a spacy doc containing 2 entities
    doc = _get_doc_spacy(nlp_spacy)

    # get a medkit doc from a spacy doc
    medkit_docs = spacy_converter.load([doc])

    assert isinstance(medkit_docs, Collection)
    assert len(medkit_docs.documents) == 1
    medkit_doc = medkit_docs.documents[0]

    assert isinstance(medkit_doc, TextDocument)
    # each span group was transferred using its name as key in segments
    assert sorted(list(medkit_doc.segments.keys())) == sorted(
        expected_labels_in_segments
    )
    # all selected spans should be included
    assert len(medkit_doc.get_annotations()) == expected_total_annotations

    # check segments
    if medkit_doc.get_annotations():
        segments = medkit_doc.get_annotations_by_label("NOUN_CHUNKS")
        # all noun-chunks were transferred
        assert len(segments) == 3
        expected_texts = sorted(["Marie Dupont", "treatment", "the central hospital"])
        texts = sorted([seg.text for seg in segments])
        assert texts == expected_texts


def test_prov(nlp_spacy):

    # create a spacy doc containing 3 entities
    doc = _get_doc_spacy(nlp_spacy)

    spacy_converter = SpacyInputConverter()
    prov_builder = ProvBuilder()
    spacy_converter.set_prov_builder(prov_builder)

    collection = spacy_converter.load([doc])
    graph = prov_builder.graph

    medkit_doc = collection.documents[0]
    entity_id = medkit_doc.entities["PERSON"][0]

    node = graph.get_node(entity_id)
    assert node.data_item_id == entity_id
    assert node.operation_id == spacy_converter.id
    assert not node.source_ids
