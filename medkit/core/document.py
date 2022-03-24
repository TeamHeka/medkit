from __future__ import annotations

__all__ = ["Collection", "Document"]

from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, cast

from medkit.core.id import generate_id
from medkit.core.annotation import Annotation
from medkit.core.store import Store, DictStore

AnnotationType = TypeVar("AnnotationType", bound=Annotation)


class Document(Generic[AnnotationType]):
    """Document holding annotations

    Annotations must be subclasses of `Annotation`."""

    def __init__(
        self,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        if doc_id is None:
            doc_id = generate_id()
        if metadata is None:
            metadata = {}
        if store is None:
            store = DictStore()

        self.id: str = doc_id
        self.store: Store = store
        self.annotation_ids: Set[str] = set()
        self.annotation_ids_by_label: Dict[str, List[str]] = {}
        self.metadata: Dict[str, Any] = metadata  # TODO: what is metadata format ?

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
            If `annotation.id` is already in Document.annotations.
        """
        id = annotation.id
        if id in self.annotation_ids:
            raise ValueError(
                f"Impossible to add this annotation.The id {id} already"
                " exists in the document"
            )

        self.annotation_ids.add(id)
        self.store.store_data_item(annotation)

        label = annotation.label
        if label not in self.annotation_ids_by_label:
            self.annotation_ids_by_label[label] = []
        self.annotation_ids_by_label[label].append(id)

    def get_annotation_by_id(self, annotation_id) -> Optional[AnnotationType]:
        if annotation_id not in self.annotation_ids:
            return None
        else:
            ann = self.store.get_data_item(annotation_id)
            return cast(AnnotationType, ann)

    def get_annotations(self) -> List[AnnotationType]:
        anns = [self.store.get_data_item(id) for id in self.annotation_ids]
        return cast(List[AnnotationType], anns)

    def get_annotations_by_label(self, label) -> List[AnnotationType]:
        anns = [
            self.store.get_data_item(id)
            for id in self.annotation_ids_by_label.get(label, [])
        ]
        return cast(List[AnnotationType], anns)


class Collection:
    """Collection of documents"""

    def __init__(self, documents: List[Document]):
        self.documents = documents
