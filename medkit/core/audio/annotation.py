__all__ = ["AudioAnnotation", "Segment"]


import abc
from typing import Any, Dict, List, Optional

from medkit.core.annotation import Annotation, Attribute
from medkit.core.audio.span import Span
from medkit.core.audio.audio_buffer import AudioBuffer


class AudioAnnotation(Annotation):
    """Base abstract class for all audio annotations"""

    @abc.abstractmethod
    def __init__(
        self,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        ann_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(label=label, attrs=attrs, ann_id=ann_id, metadata=metadata)


class Segment(AudioAnnotation):
    """Audio segment referencing part of an {class}`~medkit.core.audio.AudioDocument`.
    """

    def __init__(
        self,
        label: str,
        span: Span,
        audio: AudioBuffer,
        attrs: Optional[List[Attribute]] = None,
        ann_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
        ann_id:
            Identifier of the segment.
        metadata:
            Metadata of the segment.
        """
        super().__init__(ann_id=ann_id, label=label, attrs=attrs, metadata=metadata)

        self.span = span
        self.audio = audio
