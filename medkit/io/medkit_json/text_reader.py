__all__ = ["load_text_document", "load_text_documents", "load_text_anns"]

import json
from pathlib import Path
from typing import Iterator, Union

from medkit.core.text import TextDocument, TextAnnotation
from medkit.io.medkit_json._common import ContentType, check_header


def load_text_document(input_file: Union[str, Path]) -> TextDocument:
    """
    Load a text document from a medkit-json file generated with
    :func:`~medkit.io.medkit_json.save_text_document`.

    Parameters
    ----------
    input_file:
        Path to the medkit-json file containing the document

    Returns
    -------
    TextDocument
        The text document in the file
    """

    input_file = Path(input_file)

    with open(input_file) as fp:
        data = json.load(fp)
    check_header(data, ContentType.TEXT_DOCUMENT)
    doc = TextDocument.from_dict(data["content"])
    return doc


def load_text_documents(input_file: Union[str, Path]) -> Iterator[TextDocument]:
    """
    Load text documents from a medkit-json file generated with
    :func:`~medkit.io.medkit_json.save_text_documents`

    Parameters
    ----------
    input_file:
        Path to the medkit-json file containing the documents

    Returns
    -------
    Iterator[TextDocument]
        An iterator to the text documents in the file
    """

    input_file = Path(input_file)

    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.TEXT_DOCUMENT_LIST)

        for line in fp:
            doc_data = json.loads(line)
            doc = TextDocument.from_dict(doc_data)
            yield doc


def load_text_anns(input_file: Union[str, Path]) -> Iterator[TextAnnotation]:
    """
    Load text annotations from a medkit-json file generated with
    :func:`~medkit.io.medkit_json.save_audio_anns`

    Parameters
    ----------
    input_file:
        Path to the medkit-json file containing the annotations

    Returns
    -------
    Iterator[TextAnnotation]
        An iterator to the text annotations in the file
    """

    input_file = Path(input_file)

    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.TEXT_ANNOTATION_LIST)

        for line in fp:
            ann_data = json.loads(line)
            ann = TextAnnotation.from_dict(ann_data)
            yield ann
