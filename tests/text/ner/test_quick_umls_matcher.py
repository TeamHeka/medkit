from pathlib import Path

import pytest
import spacy.cli

from medkit.core import Collection, Attribute, Origin
from medkit.core.text import TextDocument, Span
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


def _find_entity_with_label(doc, label):
    entity_ids = doc.entities.get(label, [])
    if len(entity_ids) == 0:
        return None
    return doc.get_annotation_by_id(entity_ids[0])


def test_single_match():
    doc = TextDocument(text="The patient has asthma.")

    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, version="2021AB", language="ENG"
    )
    umls_matcher.annotate_document(doc)

    # entity
    entity = _find_entity_with_label(doc, "asthma")
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


def test_multiple_matchs():
    doc = TextDocument(text="The patient has asthma and type 1 diabetes.")

    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, version="2021AB", language="ENG"
    )
    umls_matcher.annotate_document(doc)

    # 1st entity
    entity = _find_entity_with_label(doc, "asthma")
    assert entity is not None
    assert entity.text == "asthma"
    assert entity.spans == [Span(16, 22)]

    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == _ASTHMA_CUI

    # 2d entity
    entity = _find_entity_with_label(doc, "type 1 diabetes")
    assert entity is not None
    assert entity.text == "type 1 diabetes"
    assert entity.spans == [Span(27, 42)]

    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == _DIABETES_CUI


def test_language():
    doc = TextDocument(text="Le patient fait de l'Asthme.")

    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, version="2021AB", language="FRE"
    )
    umls_matcher.annotate_document(doc)

    # entity
    entity = _find_entity_with_label(doc, "Asthme")
    assert entity is not None
    assert entity.text == "Asthme"

    # normalization attribute, same CUI as in english
    attr = entity.attrs[0]
    assert attr.label == "umls"
    assert attr.value == _ASTHMA_CUI


def test_lowercase():
    doc = TextDocument(text="Le patient fait de l'asthme.")

    # no match without lowercase flag because concept is only
    # available with leading uppercase in french
    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, version="2021AB", language="FRE"
    )
    umls_matcher.annotate_document(doc)
    assert _find_entity_with_label(doc, "asthme") is None

    # with lowercase flag, entity is found
    umls_matcher_lowercase = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL,
        language="FRE",
        version="2021AB",
        lowercase=True,
    )
    umls_matcher_lowercase.annotate_document(doc)
    entity = _find_entity_with_label(doc, "asthme")
    assert entity is not None
    assert entity.text == "asthme"


def test_ambiguous_match():
    doc = TextDocument(text="The patient has diabetes.")

    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, version="2021AB", language="ENG"
    )
    umls_matcher.annotate_document(doc)

    # "diabetes" is a term of several CUIs but only 1 entity with
    # 1 normalization attribute is created
    entity_ids = doc.entities.get("diabetes", [])
    assert len(entity_ids) == 1
    entity = doc.get_annotation_by_id(entity_ids[0])
    assert len(entity.attrs) == 1


def test_attrs_to_copy():
    doc = TextDocument(text="The patient has asthma.")
    # add attribute to input ann
    raw_ann = doc.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)[0]
    raw_ann.attrs.append(Attribute(origin=Origin(), label="negation", value=True))

    # attribute not copied
    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, version="2021AB", language="ENG"
    )
    umls_matcher.annotate_document(doc)
    entity = _find_entity_with_label(doc, "asthma")
    assert not any(a.label == "negation" for a in entity.attrs)

    # rebuild doc
    doc = TextDocument(text="The patient has asthma.")
    # add attribute to input ann
    raw_ann = doc.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)[0]
    raw_ann.attrs.append(Attribute(origin=Origin(), label="negation", value=True))

    # attribute not copied
    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL,
        version="2021AB",
        language="ENG",
        attrs_to_copy=["negation"],
    )
    umls_matcher.annotate_document(doc)
    entity = _find_entity_with_label(doc, "asthma")
    non_norm_attrs = [a for a in entity.attrs if a.label != "umls"]
    assert len(non_norm_attrs) == 1
    attr = non_norm_attrs[0]
    assert attr.label == "negation" and attr.value is True


def test_annotate_collection():
    doc = TextDocument(text="The patient has asthma.")
    collection = Collection([doc])

    umls_matcher = QuickUMLSMatcher(
        input_label=TextDocument.RAW_TEXT_LABEL, version="2021AB", language="ENG"
    )
    umls_matcher.annotate(collection)

    entity = _find_entity_with_label(doc, "asthma")
    assert entity is not None
    assert len(entity.attrs) == 1
