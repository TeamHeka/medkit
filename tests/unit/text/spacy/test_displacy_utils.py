import pytest
from spacy import displacy

from medkit.core import Attribute
from medkit.core.text import Entity, Span, ModifiedSpan, TextDocument
from medkit.text.spacy.displacy_utils import (
    medkit_doc_to_displacy,
    entities_to_displacy,
)

_TEXT = "The patient has asthma and a diabetes of type 1."


def _custom_entity_formatter(entity):
    label = entity.label
    attrs = entity.get_attrs()
    if attrs:
        attrs_string = ", ".join(f"{a.label}={a.value}" for a in attrs)
        label += f" ({attrs_string})"
    return label


_TEST_DATA = [
    # basic
    (
        [
            Entity(label="disease", spans=[Span(16, 22)], text="asthma"),
            Entity(label="disease", spans=[Span(27, 47)], text="a diabetes of type 1"),
        ],
        None,
        {
            "ents": [
                {"label": "disease", "start": 16, "end": 22},
                {"label": "disease", "start": 27, "end": 47},
            ],
            "text": _TEXT,
        },
    ),
    # entity with modified span
    (
        [
            Entity(
                label="disease",
                spans=[ModifiedSpan(length=15, replaced_spans=[Span(27, 47)])],
                text="type 1 diabetes",
            )
        ],
        None,
        {
            "ents": [
                {"label": "disease", "start": 27, "end": 47},
            ],
            "text": _TEXT,
        },
    ),
    # entity with modified span containing several replaced spans with small gaps
    (
        [
            Entity(
                label="disease",
                spans=[
                    ModifiedSpan(length=18, replaced_spans=[Span(29, 37), Span(41, 47)])
                ],
                text="type 1 diabetes",
            )
        ],
        None,
        {
            "ents": [
                {"label": "disease", "start": 29, "end": 47},
            ],
            "text": _TEXT,
        },
    ),
    # custom formatter displaying entity attributes
    (
        [
            Entity(
                label="disease",
                spans=[Span(27, 47)],
                text="a diabetes of type 1",
                attrs=[Attribute(label="cui", value="C0011854")],
            ),
        ],
        _custom_entity_formatter,
        {
            "ents": [
                {"label": "disease (cui=C0011854)", "start": 27, "end": 47},
            ],
            "text": _TEXT,
        },
    ),
]


@pytest.mark.parametrize(
    "entities,entity_formatter,expected_displacy_data",
    _TEST_DATA,
)
def test_entities_to_displacy(entities, entity_formatter, expected_displacy_data):
    displacy_data = entities_to_displacy(entities, _TEXT, entity_formatter)

    assert displacy_data == expected_displacy_data
    displacy.render(displacy_data, manual=True, style="ent")


def test_medkit_doc_to_displacy():
    doc = TextDocument(text=_TEXT)
    entity_1 = Entity(label="subject", spans=[Span(4, 11)], text="patient")
    doc.add_annotation(entity_1)
    entity_2 = Entity(label="disease", spans=[Span(16, 22)], text="asthma")
    doc.add_annotation(entity_2)
    entity_3 = Entity(
        label="disease", spans=[Span(27, 47)], text="a diabetes of type 1"
    )
    doc.add_annotation(entity_3)

    # keep only entities with "disease" label
    displacy_data = medkit_doc_to_displacy(doc, entity_labels=["disease"])
    # should have same result as directly calling entities_to_displacy()
    expected_displacy_data = entities_to_displacy([entity_2, entity_3], _TEXT)
    assert displacy_data == expected_displacy_data
