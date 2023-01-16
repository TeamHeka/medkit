from pathlib import Path

from medkit.io import medkit_json
from tests.unit.io.medkit_json._audio_common import (
    DOC_JSON_FILE,
    DOCS_JSONL_FILE,
    ANNS_JSONL_FILE,
    build_doc,
    build_docs,
    build_anns,
)


def _check_json_files_are_equal(json_file: Path, expected_json_file: Path):
    json_content = json_file.read_text().split("\n")
    expected_json_content = expected_json_file.read_text().split("\n")
    assert json_content == expected_json_content


def test_save_document(tmp_path):
    doc = build_doc()

    output_file = tmp_path / "doc.json"
    medkit_json.save_audio_document(doc, output_file)

    _check_json_files_are_equal(output_file, DOC_JSON_FILE)


def test_save_documents(tmp_path):
    docs = build_docs()

    output_file = tmp_path / "docs.jsonl"
    medkit_json.save_audio_documents(docs, output_file)

    _check_json_files_are_equal(output_file, DOCS_JSONL_FILE)


def test_save_anns(tmp_path):
    anns = build_anns()

    output_file = tmp_path / "ans.jsonl"
    medkit_json.save_audio_anns(anns, output_file)

    _check_json_files_are_equal(output_file, ANNS_JSONL_FILE)
