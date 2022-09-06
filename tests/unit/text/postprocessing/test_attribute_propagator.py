from medkit.core.text import Segment, Span
from medkit.text.ner import RegexpMatcher, RegexpMatcherRule
from medkit.text.context import NegationDetector, FamilyDetector
from medkit.text.segmentation import SyntagmaTokenizer, SentenceTokenizer
from medkit.text.postprocessing import AttributePropagator


def test_default_without_pipeline():
    text = """
        Pas de maladie. Le patient présente une maladie de grade 3.
        Son mère présente douleurs abdominales de grade 1.
        Pas de toux mais le patient a une maladie.
 """

    raw_text = Segment(label="raw_text", text=text, spans=[Span(0, len(text))])
    sentences = SentenceTokenizer().run([raw_text])

    # detecting negation in syntagmes
    syntagmes = SyntagmaTokenizer.get_example().run(sentences)
    NegationDetector(output_label="is_negated").run(syntagmes)

    # detecting family in sentences
    FamilyDetector(output_label="is_family").run(sentences)

    # detecting entities in sentences
    rules = [
        RegexpMatcherRule(
            id="id_regexp_maladie",
            label="DISEASE",
            regexp="maladie|toux|douleurs abdominales",
            version="1",
        ),
        RegexpMatcherRule(
            id="id_regexp_grade",
            label="GRADE",
            regexp="grade [0-9]",
            version="1",
        ),
    ]
    matcher = RegexpMatcher(rules=rules)
    entities = matcher.run(sentences)

    # testing attribute propagator
    propagator_1 = AttributePropagator(attr_labels=["is_negated"])
    propagator_1.run(syntagmes, entities)

    propagator_2 = AttributePropagator(attr_labels=["is_family"])
    propagator_2.run(sentences, entities)

    expected_is_negated = [True, False, False, False, False, True, False]
    expected_is_family = [False, False, False, True, True, False, False]

    entities = sorted(entities, key=lambda sp: sp.spans[0].start)

    for ent, expected_negation, expected_family in zip(
        entities, expected_is_negated, expected_is_family
    ):
        is_negated = ent.get_attrs_by_label("is_negated")[0].value
        is_family = ent.get_attrs_by_label("is_family")[0].value
        assert is_negated is expected_negation
        assert is_family is expected_family
