from __future__ import annotations

__all__ = ["AudioDocument"]

import dataclasses
import random
from typing import Any, ClassVar, Dict, List, Optional
import uuid

from medkit.core.audio.annotation import Segment
from medkit.core.audio.annotation_container import AudioAnnotationContainer
from medkit.core.audio.span import Span
from medkit.core.audio.audio_buffer import (
    AudioBuffer,
    FileAudioBuffer,
    PlaceholderAudioBuffer,
)
from medkit.core.id import generate_id
from medkit.core.store import GlobalStore


@dataclasses.dataclass(init=False)
class AudioDocument:
    """
    Document holding audio annotations.

    Attributes
    ----------
    uid:
        Unique identifier of the document.
    audio:
        Audio buffer containing the entire signal of the document.
    anns:
        Annotations of the document. Stored in an
        :class:`~.AudioAnnotationContainer` but can be passed as a list at init.
    metadata:
        Document metadata.
    raw_segment:
        Auto-generated segment containing the full unprocessed document audio.
    """

    RAW_LABEL: ClassVar[str] = "RAW_AUDIO"
    """Label to be used for raw segment"""

    uid: str
    anns: AudioAnnotationContainer
    metadata: Dict[str, Any]
    raw_segment: Segment

    def __init__(
        self,
        audio: AudioBuffer,
        anns: Optional[List[Segment]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        if anns is None:
            anns = []
        if metadata is None:
            metadata = {}
        if uid is None:
            uid = generate_id()

        self.uid = uid
        self.metadata = metadata
        self.store = GlobalStore.get_store()

        # auto-generated raw segment to hold the audio buffer
        self.raw_segment = self._generate_raw_segment(audio, uid)

        self.anns = AudioAnnotationContainer(
            doc_id=self.uid, raw_segment=self.raw_segment
        )
        for ann in anns:
            self.anns.add(ann)

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
        anns = [ann.to_dict() for ann in self.anns]
        return dict(
            uid=self.uid,
            audio=self.audio.to_dict(),
            anns=anns,
            metadata=self.metadata,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioDocument:
        if data["audio"]["class_name"] == "FileAudioBuffer":
            audio = FileAudioBuffer.from_dict(data["audio"])
        else:
            assert data["audio"]["class_name"] == "PlaceholderAudioBuffer"
            audio = PlaceholderAudioBuffer.from_dict(data["audio"])

        anns = [Segment.from_dict(ann_data) for ann_data in data["anns"]]

        return cls(
            uid=data["uid"],
            audio=audio,
            anns=anns,
            metadata=data["metadata"],
        )
