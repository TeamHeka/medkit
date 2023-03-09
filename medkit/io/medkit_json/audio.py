__all__ = [
    "load_audio_document",
    "load_audio_documents",
    "load_audio_anns",
    "save_audio_document",
    "save_audio_documents",
    "save_audio_anns",
]

import json
from pathlib import Path
from typing import Iterable, Iterator, Union

from medkit.core.audio import AudioDocument, Segment
from medkit.io.medkit_json._common import ContentType, build_header, check_header


def load_audio_document(input_file: Union[str, Path]) -> AudioDocument:
    """
    Load an audio document from a medkit-json file generated with
    :func:`~medkit.io.medkit_json.save_audio_document`

    Parameters
    ----------
    input_file:
        Path to the medkit-json file containing the document

    Returns
    -------
    AudioDocument
        The audio document in the file
    """

    input_file = Path(input_file)

    with open(input_file) as fp:
        data = json.load(fp)
    check_header(data, ContentType.AUDIO_DOCUMENT)
    doc = AudioDocument.from_dict(data["content"])
    return doc


def load_audio_documents(input_file: Union[str, Path]) -> Iterator[AudioDocument]:
    """
    Load audio documents from a medkit-json file generated with
    :func:`~medkit.io.medkit_json.save_audio_documents`

    Parameters
    ----------
    input_file:
        Path to the medkit-json file containing the documents

    Returns
    -------
    Iterator[AudioDocument]
        An iterator to the audio documents in the file
    """

    input_file = Path(input_file)

    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.AUDIO_DOCUMENT_LIST)

        for line in fp:
            doc_data = json.loads(line)
            doc = AudioDocument.from_dict(doc_data)
            yield doc


def load_audio_anns(input_file: Union[str, Path]) -> Iterator[Segment]:
    """
    Load audio annotations from a medkit-json file generated with
    :func:`~medkit.io.medkit_json.save_audio_anns`

    Parameters
    ----------
    input_file:
        Path to the medkit-json file containing the annotations

    Returns
    -------
    Iterator[Segment]
        An iterator to the audio annotations in the file
    """

    input_file = Path(input_file)

    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.AUDIO_ANNOTATION_LIST)

        for line in fp:
            ann_data = json.loads(line)
            ann = Segment.from_dict(ann_data)
            yield ann


def save_audio_document(doc: AudioDocument, output_file: Union[str, Path]):
    """
    Save an audio document into a medkit-json file.

    Parameters
    ----------
    doc:
        The audio document to save
    output_file:
        Path of the generated medkit-json file
    """

    output_file = Path(output_file)

    data = build_header(content_type=ContentType.AUDIO_DOCUMENT)
    data["content"] = doc.to_dict()
    with open(output_file, mode="w") as fp:
        json.dump(data, fp, indent=4)


def save_audio_documents(docs: Iterable[AudioDocument], output_file: Union[str, Path]):
    """
    Save audio documents into a medkit-json file.

    Parameters
    ----------
    docs:
        The audio documents to save
    output_file:
        Path of the generated medkit-json file
    """

    output_file = Path(output_file)

    header = build_header(content_type=ContentType.AUDIO_DOCUMENT_LIST)
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for doc in docs:
            doc_data = doc.to_dict()
            fp.write(json.dumps(doc_data) + "\n")


def save_audio_anns(anns: Iterable[Segment], output_file: Union[str, Path]):
    """
    Save audio annotations into a medkit-json file.

    Parameters
    ----------
    docs:
        The audio annotations to save
    output_file:
        Path of the generated medkit-json file
    """

    output_file = Path(output_file)

    header = build_header(content_type=ContentType.AUDIO_ANNOTATION_LIST)
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for ann in anns:
            ann_data = ann.to_dict()
            fp.write(json.dumps(ann_data) + "\n")
