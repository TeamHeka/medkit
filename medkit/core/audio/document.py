from __future__ import annotations

__all__ = ["AudioDocument"]

import random
from typing import Any, Dict, List, Optional
import uuid

from medkit.core.document import Document
from medkit.core.store import Store
from medkit.core.audio.annotation import AudioAnnotation, Segment
from medkit.core.audio.span import Span
from medkit.core.audio.audio_buffer import (
    AudioBuffer,
    FileAudioBuffer,
    PlaceholderAudioBuffer,
)


class AudioDocument(Document[AudioAnnotation]):
    """Document holding audio annotations."""

    RAW_LABEL = "RAW_AUDIO"

    def __init__(
        self,
        doc_id: Optional[str] = None,
        audio: Optional[AudioBuffer] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        """
        Parameters
        ----------
        doc_id:
            Document identifier, if pre-existing.
        audio:
            Audio buffer containing the whole signal for the document.
        metadata:
            Document metadata.
        store:
            Store to use for annotations.
        """
        super().__init__(doc_id=doc_id, metadata=metadata, store=store)
        self.audio: Optional[AudioBuffer] = audio

        # auto-generated RAW_AUDIO segment
        # not stored with other annotations but injected in calls to get_annotations_by_label()
        # and get_annotation_by_id()
        self.raw_segment: Optional[Segment] = self._generate_raw_segment()

    def _generate_raw_segment(self) -> Optional[Segment]:
        if self.audio is None:
            return None

        # generate deterministic uuid based on document identifier
        # so that the annotation identifier is the same if the doc identifier is the same
        rng = random.Random(self.uid)
        uid = str(uuid.UUID(int=rng.getrandbits(128)))

        return Segment(
            label=self.RAW_LABEL,
            span=Span(0.0, self.audio.duration),
            audio=self.audio,
            uid=uid,
        )

    def add_annotation(self, annotation: AudioAnnotation):
        """
        Add an annotation to the document.

        Parameters
        ----------
        annotation:
            Audio annotation to add.

        Raises
        ------
        RuntimeError
            Raised when an annotation with the same identifier is already attached to
            the document.
        """
        if annotation.label == self.RAW_LABEL:
            raise RuntimeError(
                f"Cannot add annotation with reserved label {self.RAW_LABEL}"
            )

        super().add_annotation(annotation)

    def get_annotations_by_label(self, label) -> List[AudioAnnotation]:
        # inject RAW_AUDIO segment
        if self.raw_segment is not None and label == self.RAW_LABEL:
            return [self.raw_segment]
        return super().get_annotations_by_label(label)

    def get_annotation_by_id(self, annotation_id) -> Optional[AudioAnnotation]:
        # inject RAW_AUDIO segment
        if self.raw_segment is not None and annotation_id == self.raw_segment.uid:
            return self.raw_segment
        return super().get_annotation_by_id(annotation_id)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(audio=self.audio.to_dict())
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioDocument:
        if data["audio"]["class_name"] == "FileAudioBuffer":
            audio = FileAudioBuffer.from_dict(data["audio"])
        else:
            assert data["audio"]["class_name"] == "PlaceholderAudioBuffer"
            audio = PlaceholderAudioBuffer.from_dict(data["audio"])

        annotations = [Segment.from_dict(ann_data) for ann_data in data["annotations"]]

        doc = cls(
            doc_id=data["uid"],
            audio=audio,
            metadata=data["metadata"],
        )

        for annotation in annotations:
            doc.add_annotation(annotation)

        return doc
