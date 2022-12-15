from pathlib import Path

import pytest

packaging = pytest.importorskip(
    modname="packaging", reason="packaging is not installed"
)
quickumls = pytest.importorskip(
    modname="quickumls", reason="quickumls is not installed"
)

import spacy.cli  # noqa: E402

from medkit.core import Attribute, ProvTracer  # noqa: E402
from medkit.core.text import Segment, Span  # noqa: E402
from medkit.text.ner import UMLSNormalization  # noqa: E402
from medkit.text.ner.quick_umls_matcher import QuickUMLSMatcher  # noqa: E402

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
# The sample database is kept at tests/unit/text/ner/sample_umls_data.

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
        label="sentence",
        spans=[Span(0, len(text))],
        text=text,
    )


def test_single_match():
    sentence = _get_sentence_segment("The patient has asthma.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
    entities = umls_matcher.run([sentence])

    # entity
    assert len(entities) == 1
    entity = entities[0]
    assert entity is not None
    assert entity.text == "asthma"
    assert entity.spans == [Span(16, 22)]

    # normalization attribute
    norm_attrs = entity.get_attrs_by_label("normalization")
    assert len(norm_attrs) == 1
    norm = norm_attrs[0].value
    assert isinstance(norm, UMLSNormalization)
    assert norm.cui == _ASTHMA_CUI
    assert norm.umls_version == "2021AB"
    assert norm.term == "asthma"
    assert norm.score == 1.0
    assert norm.sem_types == ["T047"]


def test_multiple_matches():
    sentence = _get_sentence_segment("The patient has asthma and type 1 diabetes.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
    entities = umls_matcher.run([sentence])

    assert len(entities) == 2

    # 1st entity (diabetes)
    entity_1 = entities[0]
    assert entity_1.label == "type 1 diabetes"
    assert entity_1.text == "type 1 diabetes"
    assert entity_1.spans == [Span(27, 42)]

    norm_1 = entity_1.get_attrs_by_label("normalization")[0].value
    assert norm_1.cui == _DIABETES_CUI
    assert norm_1.term == "type 1 diabetes"

    # 2d entity (asthma)
    entity_2 = entities[1]
    assert entity_2.label == "asthma"
    assert entity_2.text == "asthma"
    assert entity_2.spans == [Span(16, 22)]

    norm_2 = entity_2.get_attrs_by_label("normalization")[0].value
    assert norm_2.cui == _ASTHMA_CUI
    assert norm_2.term == "asthma"


def test_language():
    sentence = _get_sentence_segment("Le patient fait de l'Asthme.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="FRE")
    entities = umls_matcher.run([sentence])

    # entity
    entity = entities[0]
    assert entity.label == "Asthme"
    assert entity.text == "Asthme"

    # normalization attribute, same CUI as in english
    norm = entity.get_attrs_by_label("normalization")[0].value
    assert norm.cui == _ASTHMA_CUI
    assert norm.term == "Asthme"


def test_lowercase():
    sentence = _get_sentence_segment("Le patient fait de l'asthme.")

    # no match without lowercase flag because concept is only
    # available with leading uppercase in french
    umls_matcher = QuickUMLSMatcher(version="2021AB", language="FRE")
    entities = umls_matcher.run([sentence])
    assert len(entities) == 0

    # with lowercase flag, entity is found
    umls_matcher_lowercase = QuickUMLSMatcher(
        language="FRE", version="2021AB", lowercase=True
    )
    entities = umls_matcher_lowercase.run([sentence])
    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "asthme"
    assert entity.text == "asthme"

    norm = entity.get_attrs_by_label("normalization")[0].value
    assert norm.cui == _ASTHMA_CUI
    assert norm.term == "asthme"


def test_ambiguous_match():
    sentence = _get_sentence_segment("The patient has diabetes.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
    entities = umls_matcher.run([sentence])

    # "diabetes" is a term of several CUIs but only 1 entity with
    # 1 normalization attribute is created
    assert len(entities) == 1
    entity = entities[0]
    norm_attrs = entity.get_attrs_by_label("normalization")
    assert len(norm_attrs) == 1


def test_attrs_to_copy():
    sentence = _get_sentence_segment("The patient has asthma.")
    # copied attribute
    sentence.add_attr(Attribute(label="negation", value=True))
    # uncopied attribute
    sentence.add_attr(Attribute(label="hypothesis", value=True))

    umls_matcher = QuickUMLSMatcher(
        version="2021AB",
        language="ENG",
        attrs_to_copy=["negation"],
    )
    entity = umls_matcher.run([sentence])[0]

    norm_attrs = entity.get_attrs_by_label("normalization")
    assert len(norm_attrs) == 1
    # only negation attribute was copied
    neg_attrs = entity.get_attrs_by_label("negation")
    assert len(neg_attrs) == 1 and neg_attrs[0].value is True
    assert len(entity.get_attrs_by_label("hypothesis")) == 0


def test_prov():
    sentence = _get_sentence_segment("The patient has asthma.")

    umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")

    prov_tracer = ProvTracer()
    umls_matcher.set_prov_tracer(prov_tracer)
    entities = umls_matcher.run([sentence])

    entity = entities[0]
    entity_prov = prov_tracer.get_prov(entity.uid)
    assert entity_prov.data_item == entity
    assert entity_prov.op_desc == umls_matcher.description
    assert entity_prov.source_data_items == [sentence]

    attr = entity.get_attrs_by_label("normalization")[0]
    attr_prov = prov_tracer.get_prov(attr.uid)
    assert attr_prov.data_item == attr
    assert attr_prov.op_desc == umls_matcher.description
    assert attr_prov.source_data_items == [sentence]
