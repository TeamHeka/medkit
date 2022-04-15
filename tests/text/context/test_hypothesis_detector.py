from pathlib import Path

from medkit.core.text import Segment, Span
from medkit.text.context.hypothesis_detector import (
    HypothesisDetector,
    HypothesisDetectorRule,
)

_PATH_TO_VERBS = Path(__file__).parent / "hypothesis_verbs.yml"


def _get_syntagma_segments(syntagma_texts):
    return [
        Segment(
            label="syntagma",
            spans=[Span(0, len(text))],
            text=text,
        )
        for text in syntagma_texts
    ]


def test_single_rule():
    syntagmas = _get_syntagma_segments(["If patient has covid", "Patient has covid"])

    rule = HypothesisDetectorRule(id="id_if", regexp=r"\bif\b")
    detector = HypothesisDetector(output_label="hypothesis", rules=[rule], verbs=[])
    detector.run(syntagmas)

    # 1st syntagma is hypothesis
    assert len(syntagmas[0].attrs) == 1
    attr_1 = syntagmas[0].attrs[0]
    assert attr_1.label == "hypothesis"
    assert attr_1.value is True
    assert attr_1.metadata["rule_id"] == "id_if"

    # 2d syntagma isn't hypothesis
    assert len(syntagmas[1].attrs) == 1
    attr_2 = syntagmas[1].attrs[0]
    assert attr_2.label == "hypothesis"
    assert attr_2.value is False
    assert not attr_2.metadata


def test_multiple_rules():
    syntagmas = _get_syntagma_segments(
        ["If patient has covid", "Assuming patient has covid"]
    )

    rule_1 = HypothesisDetectorRule(id="id_if", regexp=r"\bif\b")
    rule_2 = HypothesisDetectorRule(id="id_assuming", regexp=r"\bassuming\b")
    detector = HypothesisDetector(
        output_label="hypothesis", rules=[rule_1, rule_2], verbs=[]
    )
    detector.run(syntagmas)

    # 1st syntagma is hypothesis, matched by 1st rule
    assert len(syntagmas[0].attrs) == 1
    attr_1 = syntagmas[0].attrs[0]
    assert attr_1.value is True
    assert attr_1.metadata["rule_id"] == "id_if"

    # 2d syntagma also is hypothesis, matched by 2d rule
    assert len(syntagmas[1].attrs) == 1
    attr_2 = syntagmas[1].attrs[0]
    assert attr_2.value is True
    assert attr_2.metadata["rule_id"] == "id_assuming"


def test_exclusions():
    syntagmas = _get_syntagma_segments(
        ["If patient has covid", "Even if patient has covid"]
    )

    rule = HypothesisDetectorRule(
        id="id_if",
        regexp=r"\bif\b",
        exclusion_regexps=[r"\beven\s*\bif"],
    )
    detector = HypothesisDetector(output_label="hypothesis", rules=[rule], verbs=[])
    detector.run(syntagmas)

    # 1st syntagma is hypothesis
    attr_1 = syntagmas[0].attrs[0]
    assert attr_1.value is True

    # 2d syntagma isn't hypothesis because of exclusion
    attr_2 = syntagmas[1].attrs[0]
    assert attr_2.value is False


def test_verbs():
    verbs = HypothesisDetector.load_verbs(_PATH_TO_VERBS)
    detector = HypothesisDetector(
        output_label="hypothesis",
        verbs=verbs,
        modes_and_tenses=[("indicatif", "futur"), ("conditionel", "présent")],
    )

    hyp_syntagma_texts = [
        "Il serait malade",
        "Il sera malade",
        "Il aurait le covid",
    ]
    hyp_syntagmas = _get_syntagma_segments(hyp_syntagma_texts)
    detector.run(hyp_syntagmas)

    for syntagma in hyp_syntagmas:
        attr = syntagma.attrs[0]
        assert attr.label == "hypothesis"
        assert attr.value is True

    certain_syntagmas_texts = ["Il est malade", "Il a le covid"]
    certain_syntagmas = _get_syntagma_segments(certain_syntagmas_texts)
    detector.run(certain_syntagmas)

    for syntagma in certain_syntagmas:
        attr = syntagma.attrs[0]
        assert attr.label == "hypothesis"
        assert attr.value is False


# fmt: off
# text, is_hypothesis, rule_id
_TEST_DATA = [
    # si *
    ("Si le patient est diabétique", True, "id_si"),
    ("Si oui alors le patient est diabétique", False, None),
    ("Même si le patient est diabétique", False, None),
    # all other rules without negation
    ("A condition que le patient soit diabétique", True, "id_a_condition_que"),
    ("A moins que le patient soit diabétique", True, "id_a_moins_que"),
    ("Pour peu que le patient soit diabétique", True, "id_pour_peu_que"),
    ("si tant est que patient soit diabétique", True, "id_si"),  # FIXME: expected id_si_tant_est_que
    ("Pour autant que le patient soit diabétique", True, "id_pour_autant_que"),
    ("En admettant que le patient soit diabétique", True, "id_en_admettant_que"),
    ("A supposer que le patient est diabétique", True, "id_a_supposer_que"),
    ("En supposant que  le patient soit diabétique", True, "id_en_supposant_que"),
    ("Au cas où le patient soit diabétique", True, "id_au_cas_ou"),
    # TODO suspicion
    # TODO suspectee
    ("Eventuellement, le patient serait diabétique", True, "id_eventuellement"),
    ("Le diabète est à envisager", True, "id_envisage"),
    # verb, future tense
    ("on administrera alors de l'insuline au patient", True, None),
    # verb, conditional mode
    ("on administrerait alors de l'insuline au patient", True, None),
]
# fmt: on


def test_default_rules_and_verbs():
    syntagma_texts = [d[0] for d in _TEST_DATA]
    syntagmas = _get_syntagma_segments(syntagma_texts)

    detector = HypothesisDetector(output_label="hypothesis")
    detector.run(syntagmas)

    for i in range(len(_TEST_DATA)):
        _, is_hypothesis, rule_id = _TEST_DATA[i]
        syntagma = syntagmas[i]
        assert len(syntagma.attrs) == 1
        attr = syntagma.attrs[0]
        assert attr.label == "hypothesis"

        if is_hypothesis:
            assert (
                attr.value is True
            ), f"Syntagma '{syntagma.text}' should have been detected as hypothesis"
            if rule_id is not None:
                assert attr.metadata["rule_id"] == rule_id
        else:
            assert (
                attr.value is False
            ), f"Syntagma '{syntagma.text}' shouldn't have been detected as hypothesis"
            assert not attr.metadata
