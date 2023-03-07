from __future__ import annotations

__all__ = ["AudioDocument"]

import dataclasses
import random
from typing import Any, ClassVar, Dict, List, Optional, Type
import uuid

from medkit.core.audio.annotation import Segment
from medkit.core.audio.annotation_container import AudioAnnotationContainer
from medkit.core.audio.span import Span
from medkit.core.audio.audio_buffer import (
    AudioBuffer,
    MemoryAudioBuffer,
    PlaceholderAudioBuffer,
)
from medkit.core import dict_conv
from medkit.core.id import generate_id


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

    def __init_subclass__(cls):
        raise Exception("HI")
        super().__init_subclass__()
        # type-annotated intermediary variable needed to keep mypy happy
        parent_class: Type = AudioDocument
        dict_conv.register_subclass(parent_class, cls)

    def to_dict(self) -> Dict[str, Any]:
        # convert MemoryAudioBuffer to PlaceholderAudioBuffer
        # because we can't serialize the actual signal
        if isinstance(self.audio, MemoryAudioBuffer):
            placeholder = PlaceholderAudioBuffer.from_audio_buffer(self.audio)
            audio = placeholder.to_dict()
        else:
            audio = self.audio.to_dict()
        anns = [a.to_dict() for a in self.anns]
        doc_dict = dict(
            uid=self.uid,
            audio=audio,
            anns=anns,
            metadata=self.metadata,
        )
        dict_conv.add_class_name_to_data_dict(self, doc_dict)
        return doc_dict

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> AudioDocument:
        # dispatch to subclass from_dict() if class_name in dict corresponds to a subclass
        if not dict_conv.check_class_matches_data_dict(
            AudioDocument, data, should_raise=False
        ):
            subclass = dict_conv.get_subclass_for_data_dict(AudioDocument, data)
            return subclass.from_dict(data)

        dict_conv.check_class_matches_data_dict(AudioDocument, data)
        audio = AudioBuffer.from_dict(data["audio"])
        anns = [Segment.from_dict(a) for a in data["anns"]]
        return AudioDocument(
            uid=data["uid"],
            audio=audio,
            anns=anns,
            metadata=data["metadata"],
        )
