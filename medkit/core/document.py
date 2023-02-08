__all__ = ["Document"]

from typing import Any, Dict, Generic, List, Optional, TypeVar

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

    def add_annotation(self, annotation: AnnotationType):
        """
        Add the annotation to this document

        Parameters
        ----------
        annotation:
            Annotation to add.

        Raises
        ------
        ValueError
            If `annotation.uid` is already in Document.annotations.
        """

        self.anns.add(annotation)

    def get_annotation_by_id(self, annotation_id) -> AnnotationType:
        """Returns the annotation corresponding to `annotation_id`."""
        return self.anns.get_by_id(annotation_id)

    def get_annotations(self) -> List[AnnotationType]:
        """Returns the list of annotations of the document"""
        return self.anns.get()

    def get_annotations_by_key(self, key) -> List[AnnotationType]:
        """Returns the list of annotations of the document using the processing key"""
        return self.anns.get(key=key)

    def get_annotations_by_label(self, label) -> List[AnnotationType]:
        """Returns the list of annotations of the document using the label"""
        return self.anns.get(label=label)

    def to_dict(self) -> Dict[str, Any]:
        anns = [ann.to_dict() for ann in self.anns]
        return dict(uid=self.uid, anns=anns, metadata=self.metadata)
