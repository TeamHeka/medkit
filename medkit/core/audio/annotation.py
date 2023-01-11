from __future__ import annotations

__all__ = ["AudioAnnotation", "Segment"]

import abc
from typing import Any, Dict, List, Optional, Set

from medkit.core.attribute import Attribute
from medkit.core.attribute_container import AttributeContainer
from medkit.core.audio.span import Span
from medkit.core.audio.audio_buffer import (
    AudioBuffer,
    FileAudioBuffer,
    PlaceholderAudioBuffer,
)
from medkit.core.id import generate_id
from medkit.core.store import Store


class AudioAnnotation(abc.ABC):
    """Base abstract class for all audio annotations"""

    @abc.abstractmethod
    def __init__(
        self,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
        store: Optional[Store] = None,
    ):
        """
        Parameters
        ----------
        label: str
            The annotation label
        attrs:
            The attributes of the annotation
        metadata: dict
            The dictionary containing the annotation metadata
        uid:
            The annotation identifier
        store:
            Optional shared store to hold the attributes. If none provided,
            an internal store will be used.
        """
        if uid is None:
            uid = generate_id()
        if attrs is None:
            attrs = []
        if metadata is None:
            metadata = {}

        self.uid: str = uid
        self.label: str = label
        self.metadata: Dict[str, Any] = metadata
        self.keys: Set[str] = set()

        self.attrs = AttributeContainer(store=store)
        for attr in attrs:
            self.attrs.add(attr)

    def to_dict(self) -> Dict[str, Any]:
        attrs = [a.to_dict() for a in self.attrs]
        return dict(
            uid=self.uid,
            label=self.label,
            attrs=attrs,
            metadata=self.metadata,
            class_name=self.__class__.__name__,
        )

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, annotation_dict: Dict[str, Any]) -> AudioAnnotation:
        pass

    def __repr__(self):
        return str(self.to_dict())


class Segment(AudioAnnotation):
    """Audio segment referencing part of an {class}`~medkit.core.audio.AudioDocument`.
    """

    def __init__(
        self,
        label: str,
        span: Span,
        audio: AudioBuffer,
        attrs: Optional[List[Attribute]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
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
        metadata:
            Metadata of the segment.
        uid:
            Identifier of the segment.
        store:
            Optional shared store to hold the attributes. If none provided,
            an internal store will be used.
        """
        super().__init__(
            label=label, attrs=attrs, metadata=metadata, uid=uid, store=store
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
