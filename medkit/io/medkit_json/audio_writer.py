__all__ = ["save_audio_document", "save_audio_documents", "save_audio_anns"]

import json
from pathlib import Path
from typing import Iterable, Union

from medkit.core.audio import AudioDocument, Segment
from medkit.io.medkit_json._common import ContentType, build_header


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
