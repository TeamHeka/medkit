import dataclasses
import json
import logging

import pytest
from medkit.core import Attribute
from medkit.core.text import TextDocument, Entity, Relation, Span
from medkit.io import DoccanoTask, DoccanoOutputConverter

from tests.data_utils import PATH_DOCCANO_FILES

_METADATA = {"custom_metadata": "custom", "doc_id": 1234}


# mock of UUID class used by generate_deterministic_id
@dataclasses.dataclass()
class _MockUUID:
    idx: int

    @property
    def int(self):
        return self.idx


@pytest.fixture(scope="module", autouse=True)
def _mocked_generator_id(module_mocker):
    # mock ids, force to be 0 or 1
    module_mocker.patch(
        "medkit.io.doccano.generate_deterministic_id",
        lambda ref_id: _MockUUID(int(ref_id == "e2")),
    )


def _get_doc_by_task(task: DoccanoTask):
    # get a TextDocument by task, seqlabeling and RelationExtraction use
    # the same doc, the output format changes
    doc = TextDocument(text="medkit was created in 2022")

    if task == DoccanoTask.RELATION_EXTRACTION or task == DoccanoTask.SEQUENCE_LABELING:
        medkit_anns = [
            Entity(label="ORG", spans=[Span(0, 6)], text="medkit", uid="e1"),
            Entity(label="DATE", spans=[Span(22, 26)], text="2022", uid="e2"),
            Relation(label="created_in", source_id="e1", target_id="e2", uid="r1"),
        ]

        for ann in medkit_anns:
            doc.anns.add(ann)

    elif task == DoccanoTask.TEXT_CLASSIFICATION:
        attr = Attribute(label="category", value="header")
        doc.raw_segment.attrs.add(attr)

    # only RELATION EXTRACTION has metadata
    if task == DoccanoTask.RELATION_EXTRACTION:
        doc.metadata = _METADATA
    return doc


def _load_json_file(filepath):
    with open(filepath) as fp:
        data = json.load(fp)
    return data


@pytest.mark.parametrize(
    "task",
    [
        DoccanoTask.RELATION_EXTRACTION,
        DoccanoTask.TEXT_CLASSIFICATION,
        DoccanoTask.SEQUENCE_LABELING,
    ],
)
def test_save_by_task(tmp_path, task):
    dir_path = tmp_path / task.value
    generated_json_path = dir_path / "all.jsonl"

    converter = DoccanoOutputConverter(
        task=task, attr_label="category", include_metadata=True
    )
    medkit_docs = [_get_doc_by_task(task)]
    converter.save(medkit_docs, dir_path=dir_path)

    assert dir_path.exists()
    assert generated_json_path.exists()

    data = _load_json_file(generated_json_path)
    expected_data = _load_json_file(PATH_DOCCANO_FILES / f"{task.value}.jsonl")

    assert data == expected_data


def test_warnings(tmp_path, caplog):
    task = DoccanoTask.RELATION_EXTRACTION
    converter = DoccanoOutputConverter(task=task, anns_labels=["ORG", "created_in"])
    dir_path = tmp_path / task.value

    medkit_docs = [_get_doc_by_task(task)]
    with caplog.at_level(logging.WARNING, logger="medkit.io.doccano"):
        converter.save(medkit_docs, dir_path=dir_path)
        assert "Entity source/target was no found" in caplog.text

    with pytest.raises(KeyError, match="The attribute with the corresponding .*"):
        converter = DoccanoOutputConverter(
            task=DoccanoTask.TEXT_CLASSIFICATION, attr_label="is_negated"
        )
        converter.save(medkit_docs, dir_path=dir_path)


@pytest.mark.parametrize(
    "task",
    [
        DoccanoTask.RELATION_EXTRACTION,
        DoccanoTask.TEXT_CLASSIFICATION,
        DoccanoTask.SEQUENCE_LABELING,
    ],
)
def test_save_by_task_without_metadata(tmp_path, task):
    dir_path = tmp_path / task.value
    generated_json_path = dir_path / "all.jsonl"

    converter = DoccanoOutputConverter(
        task=task, attr_label="category", include_metadata=False
    )
    medkit_docs = [_get_doc_by_task(task)]
    converter.save(medkit_docs, dir_path=dir_path)

    assert dir_path.exists()
    assert generated_json_path.exists()

    data = _load_json_file(generated_json_path)
    expected_data = _load_json_file(PATH_DOCCANO_FILES / f"{task.value}.jsonl")

    # TBD: remove metadata from expected_data
    # the test force no metadata export
    for key in _METADATA.keys():
        expected_data.pop(key, None)

    assert data == expected_data
