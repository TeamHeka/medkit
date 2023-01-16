__all__ = ["save_text_document", "save_text_documents", "save_text_anns"]

import json
from pathlib import Path
from typing import Iterable

from medkit.core import serialize
from medkit.core.text import TextDocument, TextAnnotation
from medkit.io.medkit_json._common import ContentType, Modality, build_header


def save_text_document(doc: TextDocument, output_file: Path):
    data = build_header(content_type=ContentType.DOCUMENT, modality=Modality.TEXT)
    data["content"] = serialize(doc, deep=True)
    with open(output_file, mode="w") as fp:
        json.dump(data, fp, indent=4)


def save_text_documents(docs: Iterable[TextDocument], output_file: Path):
    header = build_header(
        content_type=ContentType.DOCUMENT_LIST, modality=Modality.TEXT
    )
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for doc in docs:
            doc_data = serialize(doc, deep=True)
            fp.write(json.dumps(doc_data) + "\n")


def save_text_anns(anns: Iterable[TextAnnotation], output_file: Path):
    header = build_header(
        content_type=ContentType.ANNOTATION_LIST, modality=Modality.TEXT
    )
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for ann in anns:
            ann_data = serialize(ann, deep=True)
            fp.write(json.dumps(ann_data) + "\n")
