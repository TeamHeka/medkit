from medkit.core import Origin
from medkit.core.text import Segment, Span
from medkit.text.context.negation_detector import NegationDetector


def _get_syntagma_segments(syntama_texts):
    return [
        Segment(
            origin=Origin(),
            label="syntagma",
            spans=[Span(0, len(text))],
            text=text,
        )
        for text in syntama_texts
    ]


# fmt: off
_TEST_DATA = [
    # pas * d
    ("pas de covid", True),
    ("Pas de covid", True),  # case insensitive
    # pas * d, exclusions
    ("pas du tout de covid", True),
    ("pas de doute, le patient est atteint", False),
    ("Covid pas éliminée", False),
    ("Covid pas exclue", False),
    ("pas de soucis lors du traitement", False),
    ("pas d'objection au traitement", False),
    ("Je ne reviens pas sur ce point", False),
    # pas * pour
    ("pas suffisant pour un covid", True),
    # pas * pour, exclusions
    ("pas suffisant pour éliminer un covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    ("pas suffisant pour exclure un covid", False),
    # (ne|n') (l'|la|le * pas
    ("L'examen ne montre pas cette lésion", True),
    ("L'examen n'a pas montré cette lésion", True),
    ("L'examen ne la montre pas", False),  # FIXME: should be detected as negation, buggy regexp
    ("L'examen ne le montre pas", False),  # FIXME: should be detected as negation, buggy regexp
    ("L'examen ne l'a pas montré", True),
    # (ne|n') (l'|la|le * pas, exclusions
    ("L'examen ne laisse pas de doute sur la présence d'une lésion", False),
    ("L'examen ne permet pas d'éliminer le diagnostic covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    ("L'examen ne permet pas d'exclure le diagnostic covid", False),
    ("Le traitement n'entraîne pas de soucis", False),
    ("La proposition de traitement n'entraîne pas d'objection'", False),
    # sans
    ("sans symptome", True),
    # sans, exclusions
    ("sans doute souffrant du covid", False),
    ("sans éliminer le diagnostic covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    ("Traitement accepté sans problème", False),
    ("Traitement accepté sans soucis", False),
    ("Traitement accepté sans objection", False),
    ("Traitement accepté sans difficulté", False),
    # aucun
    ("aucun symptome", True),
    # aucun, exclusions
    ("aucun doute sur la présence d'une lésion", False),
    ("Le traitement n'entraine aucun problème", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    ("aucune objection au traitement", False),
    # élimine
    ("Covid éliminé", False),  # FIXME: should be detected as negation, buggy regexp
    # élimine, exclusions
    ("Covid pas éliminé", False),
    ("Covid pas complètement éliminé", False),
    ("sans éliminer la possibilité d'un covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    # éliminant
    ("éliminant le covid", True),
    # éliminant, exclusions
    ("n'éliminant pas le covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    # infirme
    ("Covid infirmé", True),
    # infirme, exclusions
    ("Ne permet pas d'infirmer le covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    ("Ne permet pas d'infirmer totalement le covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    ("sans infirmer la possibilité d'un covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    # infirmant
    ("infirmant le covid", True),
    # infirmant, exclusions
    ("n'infirmant pas le covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    # exclu
    ("Le covid est exclu", False),  # FIXME: should be detected as negation, buggy regexp
    ("La maladie est exclue", False),  # FIXME: should be detected as negation, buggy regexp
    # exclu, exclusions
    ("Il ne faut pas exclure le covid", False),
    ("sans exclure le covid", True),  # FIXME: shouldn't be detected as negation, buggy regexp
    # misc
    ("Jamais de covid", True),
    ("Orientant pas vers un covid", True),
    ("Ni covid ni trouble respiration", True),
    ("Covid: non", False),  # FIXME: should be detected as negation, buggy regexp
    ("Covid: aucun", True),
    ("Covid: exclu", True),
    ("Lésions: absentes", True),
    ("Covid: négatif", False),  # FIXME: should be detected as negation, buggy regexp
    ("Glycémie: normale", False),  # FIXME: should be detected as negation, buggy regexp
    ("Glycémie: pas normale", False),
]
# fmt: on


def test_negation_detector():
    syntagma_texts = [d[0] for d in _TEST_DATA]
    syntagmas = _get_syntagma_segments(syntagma_texts)

    detector = NegationDetector(output_label="negation")
    detector.process(syntagmas)

    for i in range(len(_TEST_DATA)):
        _, is_negated = _TEST_DATA[i]
        syntagma = syntagmas[i]
        assert len(syntagma.attrs) == 1
        attr = syntagma.attrs[0]
        assert attr.label == "negation"
        assert attr.value == is_negated
