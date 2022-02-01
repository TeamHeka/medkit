__all__ = ["Collection", "Document"]

import abc
import uuid

from typing import List

from medkit.core.annotation import Annotation


class Document(abc.ABC):
    def __init__(self, doc_id: str = None, metadata=None):
        if doc_id:
            self.id = doc_id
        else:
            self.id = str(uuid.uuid1())
        self.annotations = dict()
        self.operations = dict()
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
        if annotation.id not in self.annotations.keys():
            self.annotations[annotation.id] = annotation
        else:
            msg = (
                f"Impossible to add this annotation.The id {annotation.id} already"
                " exists in the document"
            )
            raise ValueError(msg)

    def get_annotation_by_id(self, annotation_id):
        return self.annotations.get(annotation_id)

    def get_annotations(self):
        return list(self.annotations.values())

    def add_operation(self, processing_desc):
        self.operations[processing_desc.id] = processing_desc


class Collection(object):
    """Collection of documents"""

    def __init__(self, documents: List[Document]):
        self.documents = documents
