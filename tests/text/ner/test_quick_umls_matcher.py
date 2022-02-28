from pathlib import Path

import pytest
import spacy.cli

from medkit.core import Collection, Origin
from medkit.core.text import TextDocument, TextBoundAnnotation, Span
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
    spacy.cli.download("en_core_web_sm")
    spacy.cli.download("fr_core_news_sm")

    yield

    # clean up global state
    QuickUMLSMatcher.clear_installs()


def _get_doc(text):
    doc = TextDocument(text=text)
    raw_text_ann = TextBoundAnnotation(
        origin=Origin(), label="RAW_TEXT", spans=[Span(0, len(text))], text=text
    )
    doc.add_annotation(raw_text_ann)
    return doc


def _find_entity_with_label(doc, label):
    entity_ids = doc.entities.get(label, [])
    if len(entity_ids) == 0:
        return None
    return doc.get_annotation_by_id(entity_ids[0])


def _find_attribute_for_entity(doc, entity):
    attribute_ids = doc.attributes.get(entity.id, [])
    if len(attribute_ids) == 0:
        return None
    return doc.get_annotation_by_id(attribute_ids[0])


def test_single_match():
    doc = _get_doc("The patient has asthma.")

    umls_matcher = QuickUMLSMatcher(
        input_label="RAW_TEXT", version="2021AB", language="ENG"
    )
    umls_matcher.annotate_document(doc)

    # entity
    entity = _find_entity_with_label(doc, "asthma")
    assert entity is not None
    assert entity.text == "asthma"
    assert entity.spans == [Span(16, 22)]

    # normalization attribute
    attribute = _find_attribute_for_entity(doc, entity)
    assert attribute is not None
    assert attribute.target_id == entity.id
    assert attribute.label == "umls"
    assert attribute.value == _ASTHMA_CUI
    assert attribute.metadata["version"] == "2021AB"
    assert attribute.metadata["score"] == 1.0
    assert attribute.metadata["sem_types"] == ["T047"]


def test_multiple_matchs():
    doc = _get_doc("The patient has asthma and type 1 diabetes.")

    umls_matcher = QuickUMLSMatcher(
        input_label="RAW_TEXT", version="2021AB", language="ENG"
    )
    umls_matcher.annotate_document(doc)

    # 1st entity
    entity = _find_entity_with_label(doc, "asthma")
    assert entity is not None
    assert entity.text == "asthma"
    assert entity.spans == [Span(16, 22)]

    attribute = _find_attribute_for_entity(doc, entity)
    assert attribute is not None
    assert attribute.target_id == entity.id
    assert attribute.value == _ASTHMA_CUI

    # 2d entity
    entity = _find_entity_with_label(doc, "type 1 diabetes")
    assert entity is not None
    assert entity.text == "type 1 diabetes"
    assert entity.spans == [Span(27, 42)]

    attribute = _find_attribute_for_entity(doc, entity)
    assert attribute is not None
    assert attribute.target_id == entity.id
    assert attribute.value == _DIABETES_CUI


def test_language():
    doc = _get_doc("Le patient fait de l'Asthme.")

    umls_matcher = QuickUMLSMatcher(
        input_label="RAW_TEXT", version="2021AB", language="FRE"
    )
    umls_matcher.annotate_document(doc)

    # entity
    entity = _find_entity_with_label(doc, "Asthme")
    assert entity is not None
    assert entity.text == "Asthme"

    # normalization attribute, same CUI as in english
    attribute = _find_attribute_for_entity(doc, entity)
    assert attribute is not None
    assert attribute.target_id == entity.id
    assert attribute.value == _ASTHMA_CUI


def test_lowercase():
    doc = _get_doc("Le patient fait de l'asthme.")

    # no match without lowercase flag because concept is only
    # available with leading uppercase in french
    umls_matcher = QuickUMLSMatcher(
        input_label="RAW_TEXT", version="2021AB", language="FRE"
    )
    umls_matcher.annotate_document(doc)
    assert _find_entity_with_label(doc, "asthme") is None

    # with lowercase flag, entity is found
    umls_matcher_lowercase = QuickUMLSMatcher(
        input_label="RAW_TEXT", language="FRE", version="2021AB", lowercase=True
    )
    umls_matcher_lowercase.annotate_document(doc)
    entity = _find_entity_with_label(doc, "asthme")
    assert entity is not None
    assert entity.text == "asthme"


def test_annotate_collection():
    doc = _get_doc("The patient has asthma.")
    collection = Collection([doc])

    umls_matcher = QuickUMLSMatcher(
        input_label="RAW_TEXT", version="2021AB", language="ENG"
    )
    umls_matcher.annotate(collection)

    entity = _find_entity_with_label(doc, "asthma")
    assert entity is not None
    attribute = _find_attribute_for_entity(doc, entity)
    assert attribute is not None
