from medkit.core import Attribute, ProvTracer
from medkit.core.text import Segment, Span
from medkit.text.ner.simstring_matcher import (
    SimstringMatcher,
    SimstringMatcherRule,
    SimstringMatcherNormalization,
)
from medkit.text.ner import UMLSNormAttribute


_TEXT = "Le patient souffre de diabète et d'asthme."


def _get_sentence_segment(text=_TEXT):
    return Segment(
        label="sentence",
        spans=[Span(10, 10 + len(text))],
        text=text,
    )


def test_basic():
    """Basic behavior"""

    sentence = _get_sentence_segment()

    rule = SimstringMatcherRule(term="diabète", label="problem")
    matcher = SimstringMatcher(rules=[rule])
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.text == "diabète"
    assert entity.spans == [Span(32, 39)]
    assert entity.label == "problem"


def test_multiple_matches():
    """Multiple matches in same segment"""

    sentence = _get_sentence_segment()

    rule_1 = SimstringMatcherRule(term="diabète", label="problem")
    rule_2 = SimstringMatcherRule(term="asthme", label="problem")
    rule_3 = SimstringMatcherRule(term="cancer", label="problem")
    rule_4 = SimstringMatcherRule(term="patient", label="person")
    matcher = SimstringMatcher(rules=[rule_1, rule_2, rule_3, rule_4])
    entities = matcher.run([sentence])

    assert len(entities) == 3

    # 1st entity (patient)
    entity_1 = entities[0]
    assert entity_1.text == "patient"
    assert entity_1.spans == [Span(13, 20)]
    assert entity_1.label == "person"

    # 2d entity (diabète)
    entity_2 = entities[1]
    assert entity_2.text == "diabète"
    assert entity_2.spans == [Span(32, 39)]
    assert entity_2.label == "problem"

    # 3d entity (asthme)
    entity_3 = entities[2]
    assert entity_3.text == "asthme"
    assert entity_3.spans == [Span(45, 51)]
    assert entity_3.label == "problem"


def test_approximate_match():
    """Fuzzy matching"""

    rule = SimstringMatcherRule(
        term="diabète",
        label="problem",
        normalizations=[
            SimstringMatcherNormalization(
                kb_name="umls", kb_version="2021AB", id="C0011849"
            )
        ],
    )
    matcher = SimstringMatcher(rules=[rule], threshold=0.1)

    sentence = _get_sentence_segment(text="Le patient souffre de diabèt et d'asthme.")
    entities = matcher.run([sentence])

    assert len(entities) == 1
    entity = entities[0]
    assert entity.text == "diabèt"


def test_normalization():
    """Normalization attribute added to entity"""
    sentence = _get_sentence_segment()

    rule = SimstringMatcherRule(
        term="diabète",
        label="problem",
        normalizations=[
            SimstringMatcherNormalization(
                kb_name="umls", kb_version="2021AB", id="C0011849"
            )
        ],
    )
    matcher = SimstringMatcher(rules=[rule])
    entities = matcher.run([sentence])

    entity = entities[0]
    norm_attrs = entity.attrs.get_norms()
    assert len(norm_attrs) == 1
    norm_attr_1 = norm_attrs[0]
    assert type(norm_attr_1) is UMLSNormAttribute
    assert norm_attr_1.kb_name == "umls"
    assert norm_attr_1.umls_version == "2021AB"
    assert norm_attr_1.cui == "C0011849"


def test_lowercase():
    """Rule term and entity in text have different case, but are matched anyway"""

    sentence = _get_sentence_segment()
    sentence.text = sentence.text.replace("asthme", "Asthme")

    rule = SimstringMatcherRule(term="ASTHME", label="problem")

    # no matches without lowercase flag
    matcher = SimstringMatcher(rules=[rule], lowercase=False)
    entities = matcher.run([sentence])
    assert len(entities) == 0

    # with lowercase flag, one match is found
    matcher = SimstringMatcher(rules=[rule], lowercase=True)
    entities = matcher.run([sentence])
    assert len(entities) == 1
    entity = entities[0]
    # lowercase not applied to entity text
    assert entity.text == "Asthme"


def test_normalize_unicode():
    """Rule term and entity in text have different non-ascii chars, but are matched anyway
    """
    sentence = _get_sentence_segment()
    sentence.text = sentence.text.replace("diabète", "dïabete")

    rule = SimstringMatcherRule(term="diabète", label="problem")

    # no matches without unicode flag
    matcher = SimstringMatcher(rules=[rule], normalize_unicode=False, threshold=1.0)
    entities = matcher.run([sentence])
    assert len(entities) == 0

    # with unicode flag, one match is found
    matcher = SimstringMatcher(rules=[rule], normalize_unicode=True, threshold=1.0)
    entities = matcher.run([sentence])
    assert len(entities) == 1
    entity = entities[0]
    # unicode normalization not applied to entity text
    assert entity.text == "dïabete"


def test_attrs_to_copy():
    sentence = _get_sentence_segment()
    # copied attribute
    neg_attr = Attribute(label="negation", value=True)
    sentence.attrs.add(neg_attr)
    # uncopied attribute
    sentence.attrs.add(Attribute(label="hypothesis", value=True))

    rule = SimstringMatcherRule(term="diabète", label="problem")

    matcher = SimstringMatcher(rules=[rule], attrs_to_copy=["negation"])
    entity = matcher.run([sentence])[0]

    # only negation attribute was copied
    neg_attrs = entity.attrs.get(label="negation")
    assert len(neg_attrs) == 1
    assert len(entity.attrs.get(label="hypothesis")) == 0

    # copied attribute has same value but new id
    copied_neg_attr = neg_attrs[0]
    assert copied_neg_attr.value == neg_attr.value
    assert copied_neg_attr.uid != neg_attr.uid


def test_prov():
    sentence = _get_sentence_segment()

    rule = SimstringMatcherRule(
        term="diabète",
        label="problem",
        normalizations=[
            SimstringMatcherNormalization(
                kb_name="umls", kb_version="2021AB", id="C0011849"
            )
        ],
    )
    matcher = SimstringMatcher(rules=[rule])

    prov_tracer = ProvTracer()
    matcher.set_prov_tracer(prov_tracer)
    entities = matcher.run([sentence])

    entity = entities[0]
    entity_prov = prov_tracer.get_prov(entity.uid)
    assert entity_prov.data_item == entity
    assert entity_prov.op_desc == matcher.description
    assert entity_prov.source_data_items == [sentence]

    attr = entity.attrs.get_norms()[0]
    attr_prov = prov_tracer.get_prov(attr.uid)
    assert attr_prov.data_item == attr
    assert attr_prov.op_desc == matcher.description
    assert attr_prov.source_data_items == [sentence]


def test_load_save_rules(tmpdir):
    rules_file = tmpdir / "rules.yml"
    rules = [
        SimstringMatcherRule(term="asthme", label="problem"),
        SimstringMatcherRule(
            term="diabète",
            label="problem",
            normalizations=[
                SimstringMatcherNormalization(
                    kb_name="umls", kb_version="2021AB", id="C0011849"
                )
            ],
        ),
    ]

    SimstringMatcher.save_rules(rules, rules_file)
    assert SimstringMatcher.load_rules(rules_file) == rules
