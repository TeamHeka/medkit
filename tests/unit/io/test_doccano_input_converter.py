import json
from zipfile import ZipFile

from medkit.io import DoccanoTask, DoccanoInputConverter


def create_doccano_files_disk(tmp_path, data, task):
    dir_path = tmp_path / task
    dir_path.mkdir()
    with ZipFile(dir_path / "file.zip", "w") as zip_file:
        json_line = json.dumps(data)
        zip_file.writestr("all.jsonl", data=json_line)


def test_relation_extraction_converter(tmp_path):
    test_line = {
        "text": "medkit was created in 2022",
        "entities": [
            {"id": 0, "start_offset": 0, "end_offset": 6, "label": "ORG"},
            {"id": 1, "start_offset": 22, "end_offset": 26, "label": "DATE"},
        ],
        "relations": [{"id": 0, "from_id": 0, "to_id": 1, "type": "created_in"}],
    }
    # prepare zip file
    task = "relation"
    create_doccano_files_disk(tmp_path, data=test_line, task=task)
    converter = DoccanoInputConverter(task=DoccanoTask.RELATION_EXTRACTION)
    documents = converter.load_from_directory_zip(dir_path=f"{tmp_path}/{task}")
    assert len(documents) == 1

    document = documents[0]
    assert len(document.anns.entities) == 2
    assert len(document.anns.relations) == 1

    entity_0 = document.anns.get(label="ORG")[0]
    entity_1 = document.anns.get(label="DATE")[0]
    relation = document.anns.get(label="created_in")[0]

    assert entity_0.text == "medkit"
    assert relation.metadata["doccano_id"] == 0
    assert relation.source_id == entity_0.uid
    assert relation.target_id == entity_1.uid


def test_sequence_labeling_converter(tmp_path):
    test_line = {
        "text": "medkit was created in 2022",
        "label": [(0, 6, "ORG"), (22, 26, "DATE")],
    }
    # prepare zip file
    task = "sequence_labeling"
    create_doccano_files_disk(tmp_path, data=test_line, task=task)
    converter = DoccanoInputConverter(task=DoccanoTask.SEQUENCE_LABELING)
    documents = converter.load_from_directory_zip(dir_path=f"{tmp_path}/{task}")
    assert len(documents) == 1

    document = documents[0]
    assert len(document.anns.entities) == 2
    assert len(document.anns.relations) == 0

    entity_0 = document.anns.get(label="ORG")[0]
    assert entity_0.text == "medkit"


def test_text_classification_converter(tmp_path):
    test_line = {"text": "medkit was created in 2022", "label": ["header"]}
    # prepare zip file
    task = "text_classification"
    create_doccano_files_disk(tmp_path, data=test_line, task=task)

    converter = DoccanoInputConverter(task=DoccanoTask.TEXT_CLASSIFICATION)
    documents = converter.load_from_directory_zip(dir_path=f"{tmp_path}/{task}")
    assert len(documents) == 1

    document = documents[0]
    assert len(document.anns.entities) == 0
    assert len(document.anns.relations) == 0

    segment = document.raw_segment
    expected_label = converter.config.category_label
    attrs = segment.attrs.get(label=expected_label)
    assert len(attrs) == 1
    assert attrs[0].value == "header"
