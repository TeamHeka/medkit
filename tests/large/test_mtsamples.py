import json
import logging
from pathlib import Path

from medkit.core.text import TextDocument
from medkit.text.preprocessing import UnicodeNormalizer, Normalizer, NormalizerRule
from medkit.text.segmentation import SentenceTokenizer
from medkit.text.ner import RegexpMatcher
from medkit.text.context import NegationDetector

_PATH_TO_MTSAMPLES = Path(__file__).parent / ".." / "data" / "mtsamples"


def _get_medkit_docs():
    path = _PATH_TO_MTSAMPLES / "mtsamples_translated.json"
    if not path.exists():
        raise FileNotFoundError(
            "For running this test, you need to have mtsamples_translated.json file in"
            " `tests/data/mtsamples` folder.\nThe file is not provided with medkit"
            " library. Please contact us to get this file."
        )
    with open(path, "r") as fdata:
        dataset = json.load(fdata)

    docs = []
    for data in dataset:
        metadata = {}
        text = ""
        for key, value in data.items():
            if key == "transcription_translated":
                text = value
            else:
                metadata[key] = value
        docs.append(TextDocument(text=text, metadata=metadata))

    return docs


def test_mt_samples_without_pipeline(caplog):
    docs = _get_medkit_docs()
    assert len(docs) == 4999

    # init and configure operations
    rules = [
        NormalizerRule(*rule)
        for rule in [
            (r"[nN]\s*°", "numéro"),
            (r"(?<=[0-9]\s)°", " degrés"),
            (r"(?<=[0-9])°", " degrés"),
            ("\u00c6", "AE"),  # ascii
            ("\u00E6", "ae"),  # ascii
            ("\u0152", "OE"),  # ascii
            ("\u0153", "oe"),  # ascii
            (r"«|»", '"'),
            ("®|©", ""),
            ("½", "1/2"),  # ascii
            ("…", "..."),  # ascii
            ("¼", "1/4"),  # ascii
        ]
    ]
    normalizer = Normalizer(output_label="norm_text", rules=rules)
    sentence_tokenizer = SentenceTokenizer()
    negation_detector = NegationDetector(output_label="negation")
    regexp_matcher = RegexpMatcher(attrs_to_copy=["negation"])

    # annotate each doc
    nb_tot_anns = 0
    for index, doc in enumerate(docs):
        anns = [doc.raw_segment]
        anns = normalizer.run(anns)
        anns = sentence_tokenizer.run(anns)
        with caplog.at_level(
            logging.WARNING, logger="medkit.text.context.negation_detector"
        ):
            negation_detector.run(anns)
            assert len(caplog.messages) == 0
        with caplog.at_level(
            logging.WARNING, logger="medkit.text.context.regexp_matcher"
        ):
            anns = regexp_matcher.run(anns)
            assert len(caplog.messages) == 0

        for ann in anns:
            doc.add_annotation(ann)

        nb_tot_anns += len(doc.get_annotations())

    assert nb_tot_anns == 13631
