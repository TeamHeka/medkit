__all__ = ["load_text_document", "load_text_documents", "load_text_anns"]

import json
from pathlib import Path
from typing import Iterator

from medkit.core.text import TextDocument, TextAnnotation
from medkit.io.medkit_json._common import ContentType, check_header


def load_text_document(input_file: Path) -> TextDocument:
    with open(input_file) as fp:
        data = json.load(fp)
    check_header(data, ContentType.TEXT_DOCUMENT)
    doc = TextDocument.from_dict(data["content"])
    return doc


def load_text_documents(input_file: Path) -> Iterator[TextDocument]:
    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.TEXT_DOCUMENT_LIST)

        for line in fp:
            doc_data = json.loads(line)
            doc = TextDocument.from_dict(doc_data)
            yield doc


def load_text_anns(input_file: Path) -> Iterator[TextAnnotation]:
    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.TEXT_ANNOTATION_LIST)

        for line in fp:
            ann_data = json.loads(line)
            ann = TextAnnotation.from_dict(ann_data)
            yield ann
