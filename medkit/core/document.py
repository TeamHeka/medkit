from __future__ import annotations

__all__ = ["Collection", "Document"]

import abc
from typing import Dict, List, TYPE_CHECKING

from medkit.core.id import generate_id

if TYPE_CHECKING:
    from medkit.core.annotation import Annotation
    from medkit.core.operation import OperationDescription


class Document(abc.ABC):
    def __init__(self, doc_id: str = None, metadata=None):
        if doc_id:
            self.id = doc_id
        else:
            self.id = generate_id()
        self.annotations: Dict[str, Annotation] = {}
        self.annotation_ids_by_label: Dict[str, List[str]] = {}
        self.operations: Dict[str, OperationDescription] = {}
        self.metadata = metadata  # TODO: what is metadata format ?

    @abc.abstractmethod
    def add_annotation(self, annotation: Annotation):
        """
        Add the annotation to this document

        Parameters
        ----------
        annotation : Annotation
            Annotation to add.

        Raises
        ------
        ValueError
            If `annotation.id` is already in Document.annotations.
        """
        id = annotation.id
        if id in self.annotations:
            raise ValueError(
                f"Impossible to add this annotation.The id {id} already"
                " exists in the document"
            )
        self.annotations[id] = annotation

        label = annotation.label
        if label not in self.annotation_ids_by_label:
            self.annotation_ids_by_label[label] = []
        self.annotation_ids_by_label[label].append(id)

    def get_annotation_by_id(self, annotation_id):
        return self.annotations.get(annotation_id)

    def get_annotations(self):
        return list(self.annotations.values())

    def get_annotations_by_label(self, label):
        return [
            self.annotations[id] for id in self.annotation_ids_by_label.get(label, [])
        ]

    def add_operation(self, operation_desc: OperationDescription):
        self.operations[operation_desc.id] = operation_desc

    def get_operations(self) -> List[OperationDescription]:
        return list(self.operations.values())


class Collection:
    """Collection of documents"""

    def __init__(self, documents: List[Document]):
        self.documents = documents
