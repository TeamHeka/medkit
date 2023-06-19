import json
from zipfile import ZipFile

import pytest

from medkit.core.prov_tracer import ProvTracer
from medkit.io import DoccanoInputConverter, DoccanoTask

TEST_LINE_BY_TASK = {
    DoccanoTask.RELATION_EXTRACTION: {
        "text": "medkit was created in 2022",
        "entities": [
            {"id": 0, "start_offset": 0, "end_offset": 6, "label": "ORG"},
            {"id": 1, "start_offset": 22, "end_offset": 26, "label": "DATE"},
        ],
        "relations": [{"id": 0, "from_id": 0, "to_id": 1, "type": "created_in"}],
    },
    DoccanoTask.SEQUENCE_LABELING: {
        "text": "medkit was created in 2022",
        "label": [(0, 6, "ORG"), (22, 26, "DATE")],
    },
    DoccanoTask.TEXT_CLASSIFICATION: {
        "text": "medkit was created in 2022",
        "label": ["header"],
    },
}


def create_doccano_files_disk(tmp_path, data, task):
    dir_path = tmp_path / task
    dir_path.mkdir()
    with ZipFile(dir_path / "file.zip", "w") as zip_file:
        json_line = json.dumps(data)
        zip_file.writestr("all.jsonl", data=json_line)


def test_relation_extraction_converter(tmp_path):
    task = DoccanoTask.RELATION_EXTRACTION
    test_line = TEST_LINE_BY_TASK[task]
    create_doccano_files_disk(tmp_path, data=test_line, task=task.value)

    converter = DoccanoInputConverter(task=task)
    documents = converter.load_from_directory_zip(dir_path=f"{tmp_path}/{task.value}")
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
    task = DoccanoTask.SEQUENCE_LABELING
    test_line = TEST_LINE_BY_TASK[task]
    create_doccano_files_disk(tmp_path, data=test_line, task=task.value)

    converter = DoccanoInputConverter(task=task)
    documents = converter.load_from_directory_zip(dir_path=f"{tmp_path}/{task.value}")
    assert len(documents) == 1

    document = documents[0]
    assert len(document.anns.entities) == 2
    assert len(document.anns.relations) == 0

    entity_0 = document.anns.get(label="ORG")[0]
    assert entity_0.text == "medkit"


def test_text_classification_converter(tmp_path):
    task = DoccanoTask.TEXT_CLASSIFICATION
    test_line = TEST_LINE_BY_TASK[task]
    create_doccano_files_disk(tmp_path, data=test_line, task=task.value)

    converter = DoccanoInputConverter(task=task)
    documents = converter.load_from_directory_zip(dir_path=f"{tmp_path}/{task.value}")
    assert len(documents) == 1

    document = documents[0]
    assert len(document.anns.entities) == 0
    assert len(document.anns.relations) == 0

    segment = document.raw_segment
    expected_label = converter.config.category_label
    attrs = segment.attrs.get(label=expected_label)
    assert len(attrs) == 1
    assert attrs[0].value == "header"


TEST_PROV_BY_TASK = [
    (DoccanoTask.RELATION_EXTRACTION, True),
    (DoccanoTask.SEQUENCE_LABELING, True),
    (DoccanoTask.TEXT_CLASSIFICATION, False),
]


@pytest.mark.parametrize(
    "task,check_prov_entity",
    TEST_PROV_BY_TASK,
)
def test_prov(tmp_path, task, check_prov_entity):
    converter = DoccanoInputConverter(task=task)
    prov_tracer = ProvTracer()
    converter.set_prov_tracer(prov_tracer)

    test_line = TEST_LINE_BY_TASK[task]
    create_doccano_files_disk(tmp_path, data=test_line, task=task.value)
    docs = converter.load_from_directory_zip(dir_path=f"{tmp_path}/{task.value}")

    doc = docs[0]
    ann = doc.anns.entities[0] if check_prov_entity else doc.raw_segment.attrs.get()[0]
    prov = prov_tracer.get_prov(ann.uid)
    assert prov.data_item == ann
    assert prov.op_desc == converter.description
    assert len(prov.source_data_items) == 0
