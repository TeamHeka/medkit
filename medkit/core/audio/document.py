from __future__ import annotations

__all__ = ["AudioDocument"]

import random
from typing import Any, Dict, Optional
import uuid

from medkit.core.document import Document
from medkit.core.store import Store, DictStore
from medkit.core.audio.annotation import AudioAnnotation, Segment
from medkit.core.audio.annotation_container import AudioAnnotationContainer
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
        audio: AudioBuffer,
        uid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        """
        Parameters
        ----------
        audio:
            Audio buffer containing the whole signal for the document.
        uid:
            Document identifier, if pre-existing.
        metadata:
            Document metadata.
        store:
            Store to use for annotations.
        """

        if store is None:
            store = DictStore()
            has_shared_store = False
        else:
            has_shared_store = True

        self.uid: str = uid
        self.store: Store = store
        self.has_shared_store = has_shared_store

        # auto-generated raw segment to hold the audio buffer
        self.raw_segment: Segment = self._generate_raw_segment(audio, self.uid)

        anns = AudioAnnotationContainer(self.raw_segment, store)
        super().__init__(
            anns=anns,
            metadata=metadata,
            uid=uid,
        )

    @classmethod
    def _generate_raw_segment(cls, audio: AudioBuffer, doc_id: str) -> Segment:
        # generate deterministic uuid based on document identifier
        # so that the annotation identifier is the same if the doc identifier is the same
        rng = random.Random(doc_id)
        uid = str(uuid.UUID(int=rng.getrandbits(128)))

        return Segment(
            label=cls.RAW_LABEL,
            span=Span(0.0, audio.duration),
            audio=audio,
            uid=uid,
        )

    @property
    def audio(self) -> AudioBuffer:
        return self.raw_segment.audio

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

        anns = [Segment.from_dict(ann_data) for ann_data in data["anns"]]

        doc = cls(
            uid=data["uid"],
            audio=audio,
            metadata=data["metadata"],
        )

        for ann in anns:
            doc.anns.add(ann)

        return doc
