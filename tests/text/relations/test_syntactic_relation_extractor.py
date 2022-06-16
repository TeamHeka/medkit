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
    (None, None, None, [["maladie", "grade"], ["level", "maladie"]]),
    (["maladie"], ["maladie"], None, []),
    (["maladie", "level"], ["maladie"], ["level"], [["maladie", "level"]]),
    (["maladie", "level"], ["maladie"], None, [["maladie", "level"]]),
    (["maladie", "level"], ["level"], None, [["level", "maladie"]]),
)


@pytest.mark.parametrize(
    "entities_labels,entities_source,entities_target,exp_source_target",
    TEST_CONFIG,
    ids=[
        "between_all_entities",
        "between_maladie",
        "between_maladie_level_source_target_not_none",
        "between_maladie_level_source_not_none",
        "between_level_maladie_source_not_none",
    ],
)
def test_relation_extractor(
    entities_labels, entities_source, entities_target, exp_source_target
):
    medkit_doc = _get_medkit_doc()
    relation_extractor = SyntacticRelationExtractor(
        name_spacy_model="fr_core_news_sm",
        entities_labels=entities_labels,
        entities_source=entities_source,
        entities_target=entities_target,
        relation_label="syntactic_dep",
        include_right_to_left_relations=True,
    )
    relation_extractor.run([medkit_doc])

    relations = medkit_doc.get_relations()
    assert len(relations) == len(exp_source_target)

    for i, relation in enumerate(relations):
        assert isinstance(relation, Relation)
        assert relation.label == "syntactic_dep"
        source_ann = medkit_doc.get_annotation_by_id(relation.source_id)
        target_ann = medkit_doc.get_annotation_by_id(relation.target_id)
        assert [source_ann.label, target_ann.label] == exp_source_target[i]


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
        entities_labels=["maladie", "level"],
        entities_source=["maladie"],
        entities_target=["level"],
        relation_label="has_level",
        include_right_to_left_relations=include_right_to_left_relations,
    )
    relation_extractor.run([medkit_doc])
    maladie_ent = medkit_doc.get_annotations_by_label("maladie")[1]
    relations_maladie = medkit_doc.get_relations_by_source_id(maladie_ent.id)
    relations = medkit_doc.get_relations()

    if include_right_to_left_relations:
        assert relations_maladie
        assert relations_maladie[0].id == relations[0].id
        assert relations_maladie[0].metadata["dep_direction"] == "right_to_left"
    else:
        assert not relations_maladie
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
