from pathlib import Path

import pytest
import spacy.cli

from medkit.core import Origin, Attribute
from medkit.core.text import Segment, Span
from medkit.text.ner.quick_umls_matcher import QuickUMLSMatcher

# QuickUMLSMatcher is a wrapper around 3d-party quickumls.core.QuickUMLS,
# which requires a QuickUMLS install to work. A QuickUMLS install can be
# created with
#
#     python -m quickumls.install <umls_installation_path> <destination_path>
#
# where <umls_installation_path> is the path to the UMLS folder containing
# the MRCONSO.RRF and MRSTY.RRF files.
#
# Because it is not allowed nof desirable to include the full UMLS
# database in the repository, we created a "sample" UMLS database
# containing only a couple of concepts, then generated several QuickUMLS
# install (with different settings) based on this database, to use in
# tests.
#
# The various QuickUMLS install generated are kept
# at tests/text/ner/quick_umls_installs.
# The sample database is kept at tests/text/ner/quick_umls_installs/sample_umls_data
# for reference but it is not directly used.

_PATH_TO_QUICK_UMLS_INSTALLS = Path(__file__).parent / "quick_umls_installs"
_PATH_TO_QUICK_UMLS_INSTALL_EN = _PATH_TO_QUICK_UMLS_INSTALLS / "en"
_PATH_TO_QUICK_UMLS_INSTALL_FR = _PATH_TO_QUICK_UMLS_INSTALLS / "fr"
_PATH_TO_QUICK_UMLS_INSTALL_FR_LOWERCASE = _PATH_TO_QUICK_UMLS_INSTALLS / "fr_lowercase"

_ASTHMA_CUI = "C0004096"
_DIABETES_CUI = "C0011854"


@pytest.fixture(scope="module", autouse=True)
def setup():
    # register QuickUMLS installs
    QuickUMLSMatcher.add_install(
        _PATH_TO_QUICK_UMLS_INSTALL_EN,
        version="2021AB",
        language="ENG",
    )
    QuickUMLSMatcher.add_install(
        _PATH_TO_QUICK_UMLS_INSTALL_FR,
        version="2021AB",
        language="FRE",
    )
    QuickUMLSMatcher.add_install(
        _PATH_TO_QUICK_UMLS_INSTALL_FR_LOWERCASE,
        version="2021AB",
        language="FRE",
        lowercase=True,
    )

    # download spacy models used by QuickUMLS
    if not spacy.util.is_package("en_core_web_sm"):
        spacy.cli.download("en_core_web_sm")
    if not spacy.util.is_package("fr_core_news_sm"):
        spacy.cli.download("fr_core_news_sm")

    yield

    # clean up global state
    QuickUMLSMatcher.clear_installs()


def _get_sentence_segment(text):
    return Segment(
        origin=Origin(),
        label="sentence",
        spans=[Span(0, len(text))],
        text=text,
    )


def _find_entity(entities, label):
    try:
        return next(e for e in entities if e.label == label)
    except StopIteration:
        return None


def test_single_match():
    sentence = _get_sentence_segment("The patient has asthma.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
    entities = umls_matcher.process([sentence])

    # entity
    assert len(entities) == 1
    entity = _find_entity(entities, "asthma")
    assert entity is not None
    assert entity.text == "asthma"
    assert entity.spans == [Span(16, 22)]

    # normalization attribute
    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == _ASTHMA_CUI
    assert attr.metadata["version"] == "2021AB"
    assert attr.metadata["score"] == 1.0
    assert attr.metadata["sem_types"] == ["T047"]


def test_multiple_matches():
    sentence = _get_sentence_segment("The patient has asthma and type 1 diabetes.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
    entities = umls_matcher.process([sentence])

    assert len(entities) == 2

    # 1st entity
    entity = _find_entity(entities, "asthma")
    assert entity is not None
    assert entity.text == "asthma"
    assert entity.spans == [Span(16, 22)]

    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == _ASTHMA_CUI

    # 2d entity
    entity = _find_entity(entities, "type 1 diabetes")
    assert entity is not None
    assert entity.text == "type 1 diabetes"
    assert entity.spans == [Span(27, 42)]

    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == _DIABETES_CUI


def test_language():
    sentence = _get_sentence_segment("Le patient fait de l'Asthme.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="FRE")
    entities = umls_matcher.process([sentence])

    # entity
    entity = _find_entity(entities, "Asthme")
    assert entity is not None
    assert entity.text == "Asthme"

    # normalization attribute, same CUI as in english
    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == _ASTHMA_CUI


def test_lowercase():
    sentence = _get_sentence_segment("Le patient fait de l'asthme.")

    # no match without lowercase flag because concept is only
    # available with leading uppercase in french
    umls_matcher = QuickUMLSMatcher(version="2021AB", language="FRE")
    entities = umls_matcher.process([sentence])
    assert _find_entity(entities, "asthme") is None

    # with lowercase flag, entity is found
    umls_matcher_lowercase = QuickUMLSMatcher(
        language="FRE", version="2021AB", lowercase=True
    )
    entities = umls_matcher_lowercase.process([sentence])
    entity = _find_entity(entities, "asthme")
    assert entity is not None
    assert entity.text == "asthme"


def test_ambiguous_match():
    sentence = _get_sentence_segment("The patient has diabetes.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
    entities = umls_matcher.process([sentence])

    # "diabetes" is a term of several CUIs but only 1 entity with
    # 1 normalization attribute is created
    assert len(entities) == 1
    entity = entities[0]
    assert len(entity.attrs) == 1


def test_attrs_to_copy():
    sentence = _get_sentence_segment("The patient has asthma.")
    sentence.attrs.append(Attribute(origin=Origin(), label="negation", value=True))

    # attribute not copied
    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
    entities = umls_matcher.process([sentence])
    entity = _find_entity(entities, "asthma")
    assert not any(a.label == "negation" for a in entity.attrs)

    # attribute not copied
    umls_matcher = QuickUMLSMatcher(
        version="2021AB",
        language="ENG",
        attrs_to_copy=["negation"],
    )
    entities = umls_matcher.process([sentence])
    entity = _find_entity(entities, "asthma")
    non_norm_attrs = [a for a in entity.attrs if a.label != "umls"]
    assert len(non_norm_attrs) == 1
    attr = non_norm_attrs[0]
    assert attr.label == "negation" and attr.value is True
