import pytest

import spacy.cli

from medkit.text.relations import SyntacticRelationExtractor
from medkit.core.text import TextDocument, Entity, Span, Relation


@pytest.fixture(scope="module", autouse=True)
def setup():
    # download french spacy model
    if not spacy.util.is_package("fr_core_news_sm"):
        spacy.cli.download("fr_core_news_sm")
    # model without parser
    if not spacy.util.is_package("xx_sent_ud_sm"):
        spacy.cli.download("xx_sent_ud_sm")


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
    (None, [["maladie", "grade"], ["level", "maladie"]]),
    (["maladie"], []),
    (["maladie", "level"], [["level", "maladie"]]),
)


@pytest.mark.parametrize(
    "label_entities,exp_labels_in_relation",
    TEST_CONFIG,
    ids=["between_all_entities", "between_maladie", "between_level_maladie"],
)
def test_relation_extractor(label_entities, exp_labels_in_relation):
    medkit_doc = _get_medkit_doc()
    relation_extractor = SyntacticRelationExtractor(
        name_spacy_model="fr_core_news_sm",
        label_entities=label_entities,
        relation_label="syntactic_dep",
        include_right_to_left_relations=True,
    )
    relation_extractor.run([medkit_doc])

    relations = medkit_doc.get_relations()
    assert len(relations) == len(exp_labels_in_relation)

    for i, relation in enumerate(relations):
        assert isinstance(relation, Relation)
        assert relation.label == "syntactic_dep"
        source_ann = medkit_doc.get_annotation_by_id(relation.source_id)
        target_ann = medkit_doc.get_annotation_by_id(relation.target_id)
        assert [source_ann.label, target_ann.label] == exp_labels_in_relation[i]


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
    level_ent = medkit_doc.get_annotations_by_label("level")[0]
    relations_level = medkit_doc.get_relations_by_source_id(level_ent.id)
    relations = medkit_doc.get_relations()

    if include_right_to_left_relations:
        assert relations_level
        assert relations_level[0].id == relations[0].id
    else:
        assert not relations_level
        assert not relations


def test_exceptions_model_not_compatible():
    with pytest.raises(OSError, match="[E941]"):
        SyntacticRelationExtractor(
            name_spacy_model="en",
        )

    with pytest.raises(ValueError, match="does not add syntax attributes"):
        SyntacticRelationExtractor(
            name_spacy_model="xx_sent_ud_sm",
        )
