__all__ = ["load_text_document", "load_text_documents", "load_text_anns"]

import json
from pathlib import Path
from typing import Iterator

from medkit.core import deserialize
from medkit.core.text import TextDocument, TextAnnotation
from medkit.io.medkit_json._common import ContentType, Modality, check_header


def load_text_document(input_file: Path) -> TextDocument:
    with open(input_file) as fp:
        data = json.load(fp)
    check_header(data, ContentType.DOCUMENT, Modality.TEXT)
    doc = deserialize(data["content"])
    return doc


def load_text_documents(input_file: Path) -> Iterator[TextDocument]:
    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.DOCUMENT_LIST, Modality.TEXT)

        for line in fp:
            doc_data = json.loads(line)
            doc = deserialize(doc_data)
            yield doc


def load_text_anns(input_file: Path) -> Iterator[TextAnnotation]:
    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.ANNOTATION_LIST, Modality.TEXT)

        for line in fp:
            ann_data = json.loads(line)
            ann = deserialize(ann_data)
            yield ann
