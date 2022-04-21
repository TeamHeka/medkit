import pytest
import spacy.cli
from medkit.core import ProvBuilder
from medkit.core.document import Collection
from medkit.core.text import Entity
from medkit.core.text import Span as MedkitSpan
from medkit.core.text.document import TextDocument
from medkit.io.spacy import SpacyInputConverter
from spacy.tokens import Span


@pytest.fixture(scope="module")
def nlp_spacy():
    # download spacy models to test sents transfer
    if not spacy.util.is_package("en_core_web_sm"):
        spacy.cli.download("en_core_web_sm")
    return spacy.load("en_core_web_sm")


TEXT_SPACY = (
    "When Sebastian Thrun started working on self-driving cars at Google in 2007, few"
    " people outside of the company took him seriously."
)

TEST_ENTS_FROM_SPACY = [(None, 3), ([], 0), (["PERSON"], 1)]


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

    # define a spacy input converted without spans or attributes
    spacy_converter = SpacyInputConverter(
        labels_ents_to_transfer=labels_ents_to_transfer,
        name_spans_to_transfer=[],
        attrs_to_transfer=[],
    )
    # create a spacy doc containing 3 entities
    doc = nlp_spacy(TEXT_SPACY)

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
        assert entity_0.text == "Sebastian Thrun"
        assert entity_0.spans == [MedkitSpan(5, 20)]
        assert entity_0.attrs == []


TEST_ATTR_FROM_SPACY = [
    (None, [1, 2, 1], [int, bool]),
    ([], [0, 0, 0], []),
    (["is_selected_ent"], [0, 1, 0], [bool]),
]


@pytest.mark.parametrize(
    "attrs_to_transfer,expected_nb_attrs,expected_class_attr_org",
    TEST_ATTR_FROM_SPACY,
    ids=["default", "no_attributes", "attr_by_label"],
)
def test_input_converter_attribute_transfer(
    nlp_spacy, attrs_to_transfer, expected_nb_attrs, expected_class_attr_org
):
    # define spacy extensions to test
    if not Span.has_extension("nb_tokens_in"):
        Span.set_extension("nb_tokens_in", default=None)

    if not Span.has_extension("is_selected_ent"):
        Span.set_extension("is_selected_ent", default=None)

    # define a spacy input converted to transfer all entities and selected attrs
    spacy_converter = SpacyInputConverter(
        labels_ents_to_transfer=None,
        name_spans_to_transfer=[],
        attrs_to_transfer=attrs_to_transfer,
    )

    # create a spacy doc containing 3 entities
    doc = nlp_spacy(TEXT_SPACY)

    # add attr in ORG entity
    for e in doc.ents:
        if e.label_ == "ORG":
            e._.set("is_selected_ent", True)

    # add default argument
    for e in doc.ents:
        e._.set("nb_tokens_in", len([token for token in e]))

    # get a medkit doc from a spacy doc
    medkit_docs = spacy_converter.load([doc])

    assert isinstance(medkit_docs, Collection)
    assert len(medkit_docs.documents) == 1
    medkit_doc = medkit_docs.documents[0]

    assert isinstance(medkit_doc, TextDocument)
    assert len(medkit_doc.entities.values()) == 3

    ents = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.entities.values()
        for id in ids
    ]
    # verify the number of attrs for each entity
    assert [len(ent.attrs) for ent in ents] == expected_nb_attrs

    # chech ORG entity
    org_entity = medkit_doc.get_annotations_by_label("ORG")[0]
    if org_entity.attrs:
        assert all(
            isinstance(attr.value, class_attr)
            for attr, class_attr in zip(org_entity.attrs, expected_class_attr_org)
        )


TEST_SEGMENTS_FROM_SPACY = [
    (None, ["SENTENCES", "NOUN_CHUNKS"], 7),
    ([], [], 0),
    (["NOUN_CHUNKS"], ["NOUN_CHUNKS"], 6),
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

    # define a spacy input converted to transfer selected spans, no entities nor attributes
    spacy_converter = SpacyInputConverter(
        labels_ents_to_transfer=[],
        name_spans_to_transfer=name_spans_to_transfer,
        attrs_to_transfer=[],
    )

    # create a spacy doc containing 3 entities
    doc = nlp_spacy(TEXT_SPACY)
    # create span groups in the spacy doc
    doc.spans["SENTENCES"] = [sent for sent in doc.sents]
    doc.spans["NOUN_CHUNKS"] = [sent for sent in doc.noun_chunks]

    # get a medkit doc from a spacy doc
    medkit_docs = spacy_converter.load([doc])

    assert isinstance(medkit_docs, Collection)
    assert len(medkit_docs.documents) == 1
    medkit_doc = medkit_docs.documents[0]

    assert isinstance(medkit_doc, TextDocument)
    # each span group was transferred using its name as key in segments
    assert list(medkit_doc.segments.keys()) == expected_labels_in_segments
    # all selected spans should be included
    assert len(medkit_doc.get_annotations()) == expected_total_annotations

    # check segments
    if medkit_doc.get_annotations():
        segments = medkit_doc.get_annotations_by_label("NOUN_CHUNKS")
        # all noun-chunks were transferred
        assert len(segments) == 6
        expected_texts = sorted(
            [
                "Sebastian Thrun",
                "self-driving cars",
                "Google",
                "few people",
                "the company",
                "him",
            ]
        )
        texts = sorted([seg.text for seg in segments])
        assert texts == expected_texts


def test_prov(nlp_spacy):

    # create a spacy doc containing 3 entities
    doc = nlp_spacy(TEXT_SPACY)

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
