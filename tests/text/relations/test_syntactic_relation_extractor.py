import pytest

import spacy.cli

from medkit.text.relations import SyntacticRelationExtractor
from medkit.core.text import TextDocument, Entity, Span, Relation


@pytest.fixture(scope="module", autouse=True)
def setup():
    # download french spacy model
    if not spacy.util.is_package("fr_core_news_sm"):
        spacy.cli.download("fr_core_news_sm")

    yield


def _get_medkit_doc():
    text = (
        "Le patient présente une douleur abdominale de grade 4, la douleur abdominale"
        " est sévère."
    )
    doc = TextDocument(text=text)
    entities = [
        Entity(spans=[Span(24, 42)], label="maladie", text="douleur abdominale"),
        Entity(spans=[Span(46, 53)], label="grade", text="grade 4"),
        Entity(spans=[Span(58, 76)], label="maladie", text="douleur abdominale"),
        Entity(spans=[Span(81, 87)], label="level", text="sévère"),
    ]
    for ent in entities:
        doc.add_annotation(ent)
    return doc


TEST_CONFIG = (
    (None, 2, [["maladie", "grade"], ["level", "maladie"]]),
    (["maladie"], 0, [[]]),
    (["maladie", "level"], 1, [["level", "maladie"]]),
)


@pytest.mark.parametrize(
    "label_entities,nb_exp_relations,exp_relations_labels",
    TEST_CONFIG,
    ids=["between_all_entities", "between_maladie", "between_level_maladie"],
)
def test_relation_extractor(label_entities, nb_exp_relations, exp_relations_labels):
    medkit_doc = _get_medkit_doc()
    relation_extractor = SyntacticRelationExtractor(
        name_spacy_model="fr_core_news_sm",
        label_entities=label_entities,
        relation_label="syntactic_dep",
        include_right_to_left_relations=True,
    )
    relation_extractor.run([medkit_doc])

    relations = [
        medkit_doc.get_annotation_by_id(id)
        for ids in medkit_doc.relations.values()
        for id in ids
    ]
    assert len(relations) == nb_exp_relations

    if nb_exp_relations:
        for i, relation in enumerate(relations):
            assert isinstance(relation, Relation)
            assert relation.label == "syntactic_dep"
            source_ann = medkit_doc.get_annotation_by_id(relation.source_id)
            target_ann = medkit_doc.get_annotation_by_id(relation.target_id)
            assert [source_ann.label, target_ann.label] == exp_relations_labels[i]
            # check relation is in entity
            assert relation.id in source_ann.relations
            assert relation.id in target_ann.relations


@pytest.mark.parametrize(
    "include_right_to_left_relations",
    [True, False],
    ids=["with_right_to_left_relations", "without_right_to_left_relations"],
)
def test_include_right_to_left_relations(include_right_to_left_relations):
    # in the phrase : 'la douleur abdominale est sévère' the relation goes from
    # level (severe) to maladie (douleur abdominale), it is a right-to-left relation
    medkit_doc = _get_medkit_doc()
    relation_extractor = SyntacticRelationExtractor(
        name_spacy_model="fr_core_news_sm",
        label_entities=["maladie", "level"],
        relation_label="is_dependent",
        include_right_to_left_relations=include_right_to_left_relations,
    )
    relation_extractor.run([medkit_doc])
    maladie_ent = medkit_doc.get_annotations_by_label("maladie")[1]
    relation_id = medkit_doc.relations.get("is_dependent", [])

    if include_right_to_left_relations:
        assert relation_id
        assert relation_id[0] in maladie_ent.relations
    else:
        assert not relation_id
        assert not maladie_ent.relations


def test_exception_model_not_found():
    with pytest.raises(OSError, match="Model for language was not found."):
        SyntacticRelationExtractor(
            name_spacy_model="en",
        )
