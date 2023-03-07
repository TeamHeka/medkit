__all__ = ["save_audio_document", "save_audio_documents", "save_audio_anns"]

import json
from pathlib import Path
from typing import Iterable

from medkit.core.audio import AudioDocument, Segment
from medkit.io.medkit_json._common import ContentType, Modality, build_header


def save_audio_document(doc: AudioDocument, output_file: Path):
    data = build_header(content_type=ContentType.DOCUMENT, modality=Modality.AUDIO)
    data["content"] = doc.to_dict()
    with open(output_file, mode="w") as fp:
        json.dump(data, fp, indent=4)


def save_audio_documents(docs: Iterable[AudioDocument], output_file: Path):
    header = build_header(
        content_type=ContentType.DOCUMENT_LIST, modality=Modality.AUDIO
    )
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for doc in docs:
            doc_data = doc.to_dict()
            fp.write(json.dumps(doc_data) + "\n")


def save_audio_anns(anns: Iterable[Segment], output_file: Path):
    header = build_header(
        content_type=ContentType.ANNOTATION_LIST, modality=Modality.AUDIO
    )
    with open(output_file, mode="w") as fp:
        fp.write(json.dumps(header) + "\n")

        for ann in anns:
            ann_data = ann.to_dict()
            fp.write(json.dumps(ann_data) + "\n")
