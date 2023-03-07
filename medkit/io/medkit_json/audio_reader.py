__all__ = ["load_audio_document", "load_audio_documents", "load_audio_anns"]

import json
from pathlib import Path
from typing import Iterator

from medkit.core.audio import AudioDocument, Segment
from medkit.io.medkit_json._common import ContentType, check_header


def load_audio_document(input_file: Path) -> AudioDocument:
    with open(input_file) as fp:
        data = json.load(fp)
    check_header(data, ContentType.AUDIO_DOCUMENT)
    doc = AudioDocument.from_dict(data["content"])
    return doc


def load_audio_documents(input_file: Path) -> Iterator[AudioDocument]:
    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.AUDIO_DOCUMENT_LIST)

        for line in fp:
            doc_data = json.loads(line)
            doc = AudioDocument.from_dict(doc_data)
            yield doc


def load_audio_anns(input_file: Path) -> Iterator[Segment]:
    with open(input_file) as fp:
        line = fp.readline()
        data = json.loads(line)
        check_header(data, ContentType.AUDIO_ANNOTATION_LIST)

        for line in fp:
            ann_data = json.loads(line)
            ann = Segment.from_dict(ann_data)
            yield ann
