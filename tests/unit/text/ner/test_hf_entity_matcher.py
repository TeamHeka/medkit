import pytest

from medkit.core import Attribute, ProvTracer
from medkit.core.text import Segment, Span
from medkit.text.ner.hf_entity_matcher import HFEntityMatcher


_MODEL = "samrawal/bert-base-uncased_clinical-ner"
_SPAN_OFFSET = 10


def _get_sentence_segment(text):
    return Segment(
        label="sentence",
        spans=[Span(_SPAN_OFFSET, _SPAN_OFFSET + len(text))],
        text=text,
    )


@pytest.fixture(scope="module")
def matcher():
    return HFEntityMatcher(model=_MODEL)


def test_single_match(matcher):
    """Basic behavior, single match in one input segment"""

    sentence = _get_sentence_segment("The patient has asthma.")
    entities = matcher.run([sentence])
    assert len(entities) == 1

    # entity
    entity = entities[0]
    assert entity.label == "problem"
    assert entity.text == "asthma"
    assert entity.spans == [Span(26, 32)]

    # score attribute
    attrs = entity.get_attrs_by_label("score")
    assert len(attrs) == 1
    attr = attrs[0]
    assert attr.label == "score"
    assert 0.0 <= attr.value <= 1.0


def test_multiple_matches(matcher):
    """Basic behavior, multiple matches in multiple input segments"""

    sentence_1 = _get_sentence_segment("The patient has asthma and is using ventoline.")
    sentence_2 = _get_sentence_segment("The patient has diabetes.")
    sentences = [sentence_1, sentence_2]
    entities = matcher.run(sentences)
    assert len(entities) == 3

    # 1st entity
    entity_1 = entities[0]
    assert entity_1.label == "problem"
    assert entity_1.text == "asthma"
    assert entity_1.spans == [Span(26, 32)]

    # 2nd entity
    entity_2 = entities[1]
    assert entity_2.label == "treatment"
    assert entity_2.text == "ventoline"
    assert entity_2.spans == [Span(46, 55)]

    # 3rd entity
    entity_3 = entities[2]
    assert entity_3.label == "problem"
    assert entity_3.text == "diabetes"
    assert entity_3.spans == [Span(26, 34)]


def test_attrs_to_copy():
    """Copying of selected attributes from input segment to created entity"""

    sentence = _get_sentence_segment("The patient has asthma.")
    # copied attribute
    sentence.add_attr(Attribute(label="negation", value=False))
    # uncopied attribute
    sentence.add_attr(Attribute(label="hypothesis", value=False))

    matcher = HFEntityMatcher(model=_MODEL, attrs_to_copy=["negation"])
    entity = matcher.run([sentence])[0]

    assert len(entity.get_attrs_by_label("score")) == 1
    # only negation attribute was copied
    neg_attrs = entity.get_attrs_by_label("negation")
    assert len(neg_attrs) == 1 and neg_attrs[0].value is False
    assert len(entity.get_attrs_by_label("hypothesis")) == 0


def test_prov(matcher):
    """Generated provenance nodes"""

    # use file containing voice signal
    sentence_1 = _get_sentence_segment("The patient has asthma and is using ventoline.")
    sentence_2 = _get_sentence_segment("The patient has diabetes.")
    sentences = [sentence_1, sentence_2]

    prov_tracer = ProvTracer()
    matcher.set_prov_tracer(prov_tracer)
    entities = matcher.run(sentences)
    assert len(entities) == 3

    # data item id and operation id are correct
    entity_1 = entities[0]
    prov_1 = prov_tracer.get_prov(entity_1.id)
    assert prov_1.data_item == entity_1
    assert prov_1.op_desc == matcher.description

    # 1st and 2nd entities have 1st sentence as source
    assert prov_1.source_data_items == [sentence_1]
    entity_2 = entities[1]
    prov_2 = prov_tracer.get_prov(entity_2.id)
    assert prov_2.source_data_items == [sentence_1]

    # 3d entity has 2nd sentence as source
    entity_3 = entities[2]
    prov_3 = prov_tracer.get_prov(entity_3.id)
    assert prov_3.source_data_items == [sentence_2]
