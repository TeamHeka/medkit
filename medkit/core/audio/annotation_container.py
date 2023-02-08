__all__ = ["AudioAnnotationContainer"]

from typing import List, Optional

from medkit.core.annotation_container import AnnotationContainer
from medkit.core.store import Store
from medkit.core.audio.annotation import AudioAnnotation, Segment


class AudioAnnotationContainer(AnnotationContainer[AudioAnnotation]):
    """
    Manage a list of audio annotations belonging to an audio document.

    This behaves more or less like a list: calling `len()` and iterating are
    supported. Additional filtering is available through the `get()` method.

    Also provides handling of raw segment.
    """

    def __init__(self, raw_segment: Segment, store: Optional[Store] = None):
        super().__init__(store)

        # auto-generated RAW_AUDIO segment
        # not stored with other annotations but injected in calls to get()
        # and get_by_id()
        self.raw_segment = raw_segment

    def add(self, ann: AudioAnnotation):
        if ann.label == self.raw_segment.label:
            raise RuntimeError(
                f"Cannot add annotation with reserved label {self.raw_segment.label}"
            )

        super().add(ann)

    def get(
        self, *, label: Optional[str] = None, key: Optional[str] = None
    ) -> List[AudioAnnotation]:
        # inject raw segment
        if label == self.raw_segment.label and key is None:
            return [self.raw_segment]
        return super().get(label=label, key=key)

    def get_by_id(self, uid) -> AudioAnnotation:
        # inject raw segment
        if uid == self.raw_segment.uid:
            return self.raw_segment
        return super().get_by_id(uid)
