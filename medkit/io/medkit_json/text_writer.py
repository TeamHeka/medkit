__all__ = ["save_text_document", "save_text_documents", "save_text_anns"]

import json
from pathlib import Path
from typing import Iterable

from medkit.core.text import TextDocument, TextAnnotation
from medkit.io.medkit_json._common import ContentType, build_header


def save_text_document(doc: TextDocument, output_file: Path):
    """
    Save a text document into a medkit-json file.

    Parameters
    ----------
    doc:
        The text document to save
    output_file:
        Path of the generated medkit-json file
    """

    data = build_header(content_type=ContentType.TEXT_DOCUMENT)
    data["content"] = doc.to_dict()
    with open(output_file, mode="w") as fp:
        json.dump(data, fp, indent=4)


def save_text_documents(docs: Iterable[TextDocument], output_file: Path):
    """
    Save text documents into a medkit-json file.

    Parameters
    ----------
    docs:
        The text documents to save
    output_file:
        Path of the generated medkit-json file
    """

    header = build_header(content_type=ContentType.TEXT_DOCUMENT_LIST)
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for doc in docs:
            doc_data = doc.to_dict()
            fp.write(json.dumps(doc_data) + "\n")


def save_text_anns(anns: Iterable[TextAnnotation], output_file: Path):
    """
    Save text annotations into a medkit-json file.

    Parameters
    ----------
    docs:
        The text annotations to save
    output_file:
        Path of the generated medkit-json file
    """

    header = build_header(content_type=ContentType.TEXT_ANNOTATION_LIST)
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for ann in anns:
            ann_data = ann.to_dict()
            fp.write(json.dumps(ann_data) + "\n")
