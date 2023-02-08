__all__ = ["Document"]

from typing import Any, Dict, Generic, Optional, TypeVar

from medkit.core.id import generate_id
from medkit.core.annotation import Annotation
from medkit.core.annotation_container import AnnotationContainer

AnnotationType = TypeVar("AnnotationType", bound=Annotation)


class Document(Generic[AnnotationType]):
    """Document holding annotations

    Annotations must be subclasses of `Annotation`."""

    def __init__(
        self,
        anns: Optional[AnnotationContainer[AnnotationType]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        anns:
            The document annotations, in an `AnnotationContainer`.
        metadata:
            Metadata of the document
        uid:
            Id of the document in UUID format. Auto-generated if none provided
        """
        if anns is None:
            anns = AnnotationContainer()
        if uid is None:
            uid = generate_id()
        if metadata is None:
            metadata = {}

        self.metadata: Dict[str, Any] = metadata  # TODO: what is metadata format ?

        self.anns = anns

    def to_dict(self) -> Dict[str, Any]:
        anns = [ann.to_dict() for ann in self.anns]
        return dict(uid=self.uid, anns=anns, metadata=self.metadata)
