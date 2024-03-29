from medkit.io import medkit_json
from tests.unit.io.medkit_json._text_common import (
    DOC_JSON_FILE,
    DOCS_JSONL_FILE,
    ANNS_JSONL_FILE,
    SPLIT_DOC_JSON_FILE,
    SPLIT_DOC_ANNS_JSONL_FILE,
    build_doc,
    build_docs,
    build_anns,
)


def test_load_document():
    doc = medkit_json.load_text_document(DOC_JSON_FILE)

    expected_doc = build_doc()
    assert doc == expected_doc


def test_load_documents():
    docs = medkit_json.load_text_documents(DOCS_JSONL_FILE)

    expected_docs = build_docs()
    assert list(docs) == expected_docs


def test_load_anns():
    anns = medkit_json.load_text_anns(ANNS_JSONL_FILE)

    expected_anns = build_anns()
    assert list(anns) == expected_anns


def test_load_document_split():
    doc = medkit_json.load_text_document(SPLIT_DOC_JSON_FILE, SPLIT_DOC_ANNS_JSONL_FILE)

    expected_doc = build_doc()
    assert doc == expected_doc
