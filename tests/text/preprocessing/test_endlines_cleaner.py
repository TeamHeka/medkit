import pytest

from medkit.core.text import Span, Segment
from medkit.text.preprocessing.endlines_cleaner import EndlinesCleaner

TEST_CONFIG = [
    (
        "Nom patient : la Mme. Marie Dupont, date le     .24 avril .    pour un"
        " probleme",
        "Nom patient : la Mme  Marie Dupont, date le 24 avril pour un probleme",
    ),
    (
        "Traitement : (N.B. : absence de notion de la prescription d'une HBPM)\n\n\n à"
        " dose curative dès cet appel.",
        "Traitement : à dose curative dès cet appel ; N B. : absence de notion de la"
        " prescription d'une HBPM.",
    ),
    (
        "Résultats : examen reviens (+)",
        "Résultats : examen reviens  positif ",
    ),
    (
        "Le patient\n\n\nreviens\n\nle 4 d\n\n\n\navril",
        "Le patient reviens le 4 d avril",
    ),
]


def _get_raw_segment(text):
    return Segment(
        label="RAW_TEXT",
        spans=[Span(0, len(text))],
        text=text,
    )


@pytest.mark.parametrize("text,expected_text", TEST_CONFIG)
def test_default_cleaner(text, expected_text):

    cleaner = EndlinesCleaner()
    raw_segment = _get_raw_segment(text)
    clean_ann = cleaner.run([raw_segment])[0]

    assert clean_ann.text == expected_text
