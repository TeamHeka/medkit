import pytest

import spacy
from spacy.tokens import Doc
from spacy.tokens import Span as SpacySpan

from medkit.core import ProvBuilder
from medkit.core.text import Entity, Span, TextDocument
from medkit.text.spacy import SpacyDocPipeline


@pytest.fixture(scope="module")
def nlp_spacy():
    return spacy.blank("en")


@spacy.Language.component(
    "_attribute_adder",
    requires=["doc.ents"],
    retokenizes=False,
)
def _custom_component(spacy_doc: Doc) -> Doc:
    """Mock spacy component, this component adds 'is_from_medkit' extension
    in each entity, and a DATE"""
    # set an attribute in spacy
    if not SpacySpan.has_extension("is_from_medkit"):
        SpacySpan.set_extension("is_from_medkit", default=None)
    # add DATE entity
    spacy_doc.ents = list(spacy_doc.ents) + [spacy_doc.char_span(36, 40, label="DATE")]

    for ent in spacy_doc.ents:
        # check if medkit_id was set up
        value = ent._.get("medkit_id") is not None
        ent._.set("is_from_medkit", value)

    return spacy_doc


@pytest.fixture(scope="module")
def nlp_spacy_modified():
    # download spacy models to test sents transfer
    nlp = spacy.blank("en")
    nlp.add_pipe("_attribute_adder", last=True)
    # check if component was added in spacy
    assert "_attribute_adder" in nlp.pipe_names
    return nlp


TEXT = "The patient visited the hospital in 2005 for an unknown degree of influenza."

# entities created by medkit
ENTITIES = [
    ("disease", (66, 75), "influenza"),
    ("grade", (48, 62), "unknown degree"),
]


def _get_doc():
    medkit_doc = TextDocument(text=TEXT)
    for ent in ENTITIES:
        entity = Entity(
            label=ent[0],
            spans=[Span(ent[1][0], ent[1][1])],
            text=ent[2],
            attrs=[],
        )
        medkit_doc.add_annotation(entity)
    return medkit_doc


def test_default_pipeline(nlp_spacy):
    spacydoc_pipeline = SpacyDocPipeline(nlp=nlp_spacy)

    # add original annotations
    medkit_doc = _get_doc()
    assert len(medkit_doc.get_annotations()) == 2
    assert "DATE" not in medkit_doc.entities.keys()

    # run the pipeline
    spacydoc_pipeline.run([medkit_doc])

    entities = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.entities.values()
        for id in ids
    ]

    # entities have no attrs
    assert all(len(ent.attrs) == 0 for ent in entities)


def test_default_with_modified_pipeline(nlp_spacy_modified):
    # adding a component in spacy
    nlp = nlp_spacy_modified

    # created a docpipeline using the new nlp object
    spacydoc_pipeline = SpacyDocPipeline(nlp=nlp)

    # create original annotations
    medkit_doc = _get_doc()
    assert len(medkit_doc.get_annotations()) == 2
    assert "DATE" not in medkit_doc.entities.keys()

    entities = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.entities.values()
        for id in ids
    ]
    # original entities have no attrs
    assert all(len(ent.attrs) == 0 for ent in entities)
    # id to compare
    disease_original = medkit_doc.get_annotations_by_label("disease")[0]

    # run the pipeline
    spacydoc_pipeline.run([medkit_doc])

    # spacy add a new annotation with 'DATE' as label
    assert len(medkit_doc.get_annotations()) == 3
    entities = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.entities.values()
        for id in ids
    ]

    # spacy_doc adds 1 attribute
    assert all(len(ent.attrs) == 1 for ent in entities)

    # check new entity
    new_annotation = medkit_doc.get_annotations_by_label("DATE")[0]
    assert "DATE" in medkit_doc.entities.keys()
    assert new_annotation.label == "DATE"
    assert new_annotation.text == "2005"
    assert new_annotation.attrs[0].label == "is_from_medkit"
    assert not new_annotation.attrs[0].value

    # check original entity
    # this entity comes from medkit; medkit_id was set up in the conversion phase,
    # so, 'attribute_adder' defines 'is_from_medkit' as True (cf. _custom_component)
    disease = medkit_doc.get_annotations_by_label("disease")[0]
    assert disease.attrs[0].label == "is_from_medkit"
    assert disease.attrs[0].value

    # check disease is the same entity
    disease_original_after = medkit_doc.get_annotations_by_label("disease")[0]
    assert disease_original is disease_original_after


def test_prov(nlp_spacy_modified):
    # adding a component in spacy
    nlp = nlp_spacy_modified

    # created a docpipeline using the new nlp object
    spacydoc_pipeline = SpacyDocPipeline(nlp=nlp)
    prov_builder = ProvBuilder()
    spacydoc_pipeline.set_prov_builder(prov_builder)

    # create original annotations
    medkit_doc = _get_doc()
    # run the pipeline
    spacydoc_pipeline.run([medkit_doc])

    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    # check new entity
    graph = prov_builder.graph
    entity_id = medkit_doc.entities["DATE"][0]
    entity = medkit_doc.get_annotation_by_id(entity_id)
    node = graph.get_node(entity_id)
    assert node.data_item_id == entity_id
    assert node.operation_id == spacydoc_pipeline.id
    assert node.source_ids == [raw_annotation.id]

    attribute = entity.attrs[0]
    attr = graph.get_node(attribute.id)
    assert attr.data_item_id == attribute.id
    assert attr.operation_id == spacydoc_pipeline.id
    # it is a new entity, medkit object origin was raw_ann
    assert attr.source_ids == [raw_annotation.id]

    # check new attr entity
    entity_id = medkit_doc.entities["disease"][0]
    entity = medkit_doc.get_annotation_by_id(entity_id)

    attribute = entity.attrs[0]
    attr = graph.get_node(attribute.id)
    assert attr.data_item_id == attribute.id
    assert attr.operation_id == spacydoc_pipeline.id
    # it is a medkit entity, medkit object origin was entity
    assert attr.source_ids == [entity_id]
