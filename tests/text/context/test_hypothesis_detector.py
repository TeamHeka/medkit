from pathlib import Path

from medkit.core.text import Segment, Span
from medkit.text.context.hypothesis_detector import HypothesisDetector

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
# text, is_hypothesis
_TEST_DATA = [
    # si *
    ("Si le patient est diabétique", True),
    ("Si oui alors le patient est diabétique", False),
    ("Même si le patient est diabétique", False),
    # all other rules without negation
    ("A condition que le patient soit diabétique", True),
    ("A moins que le patient soit diabétique", True),
    ("Pour peu que le patient soit diabétique", True),
    ("si tant est que patient soit diabétique", True),
    ("Pour autant que le patient soit diabétique", True),
    ("En admettant que le patient soit diabétique", True),
    ("A supposer que le patient est diabétique", True),
    ("En supposant que  le patient soit diabétique", True),
    ("Au cas où le patient soit diabétique", True),
    # TODO suspicion
    # TODO suspectee
    ("Eventuellement, le patient serait diabétique", True),
    ("Le diabète est à envisager", True),
    # verb, future tense
    ("on administrera alors de l'insuline au patient", True),
    # verb, conditional mode
    ("on administrerait alors de l'insuline au patient", True),
]
# fmt: on


def test_default_rules_and_verbs():
    syntagma_texts = [d[0] for d in _TEST_DATA]
    syntagmas = _get_syntagma_segments(syntagma_texts)

    detector = HypothesisDetector(output_label="hypothesis")
    detector.run(syntagmas)

    for i in range(len(_TEST_DATA)):
        _, is_hypothesis = _TEST_DATA[i]
        syntagma = syntagmas[i]
        assert len(syntagma.attrs) == 1
        attr = syntagma.attrs[0]
        assert attr.label == "hypothesis"

        if is_hypothesis:
            assert (
                attr.value is True
            ), f"Syntagma '{syntagma.text}' should have been detected as hypothesis"
        else:
            assert (
                attr.value is False
            ), f"Syntagma '{syntagma.text}' shouldn't have been detected as hypothesis"
