__all__ = ["AudioAnnotation", "Segment"]


import abc
from typing import Any, Dict, List, Optional

from medkit.core.annotation import Annotation, Attribute
from medkit.core.audio.span import Span
from medkit.core.audio.audio_buffer import (
    AudioBuffer,
    FileAudioBuffer,
    PlaceholderAudioBuffer,
)
from medkit.core.store import Store


class AudioAnnotation(Annotation):
    """Base abstract class for all audio annotations"""

    @abc.abstractmethod
    def __init__(
        self,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        uid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        super().__init__(
            label=label, attrs=attrs, uid=uid, metadata=metadata, store=store
        )

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(span=self.span.to_dict(), audio=self.audio.to_dict())
        return data


class Segment(AudioAnnotation):
    """Audio segment referencing part of an {class}`~medkit.core.audio.AudioDocument`.
    """

    def __init__(
        self,
        label: str,
        span: Span,
        audio: AudioBuffer,
        attrs: Optional[List[Attribute]] = None,
        uid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        """
        Parameters
        ----------
        label:
            Label of the segment.
        span:
            Span (in seconds) referenced by the segment
        audio:
            The audio signal of the segment. It must be consistent with the span,
            in the sense that it must correspond to the audio signal of the document
            at the span boundaries. But it can be a modified, processed version of this
            audio signal.
        attrs:
            Attributes of the segment.
        uid:
            Identifier of the segment.
        metadata:
            Metadata of the segment.
        store:
            Optional shared store to hold the attributes. If none provided,
            an internal store will be used.
        """
        super().__init__(
            uid=uid, label=label, attrs=attrs, metadata=metadata, store=store
        )

        self.span = span
        self.audio = audio

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(span=self.span.to_dict(), audio=self.audio.to_dict())
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        span = Span.from_dict(data["span"])

        if data["audio"]["class_name"] == "FileAudioBuffer":
            audio = FileAudioBuffer.from_dict(data["audio"])
        else:
            assert data["audio"]["class_name"] == "PlaceholderAudioBuffer"
            audio = PlaceholderAudioBuffer.from_dict(data["audio"])

        attrs = [Attribute.from_dict(a) for a in data["attrs"]]

        return cls(
            label=data["label"],
            span=span,
            audio=audio,
            attrs=attrs,
            uid=data["uid"],
            metadata=data["metadata"],
        )
