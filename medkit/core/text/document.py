from __future__ import annotations

__all__ = ["TextDocument"]

import typing

from medkit.core.document import Document
from medkit.core.text.annotation import TextBoundAnnotation, Entity, Relation, Attribute

if typing.TYPE_CHECKING:
    from medkit.core.annotation import Annotation


class TextDocument(Document):
    def __init__(self, doc_id: str = None, text: str = None, metadata=None):
        """
        Initializes the text document

        The method uses the abstract class Document to initialize a part
        and creates dictionary views for accessing entities, attributes and
        relations.

        Parameters
        ----------
        doc_id: str, Optional
            Document identifier. If None, an uuid is generated.
        text: str, Optional
            Document text
        metadata: dict  # TODO
            Document metadata

        """
        super().__init__(doc_id, metadata)
        self.text = text
        self.segments = dict()  # Key: label
        self.entities = dict()  # Key: label
        self.relations = dict()  # Key: TODO : determine the key
        self.attributes = dict()  # Key : target_id

    def add_annotation(self, annotation: Annotation):
        """
        Add the annotation to this document

        The method uses the abstract class method to add the annotation
        in the Document.
        It also adds the annotation id to the corresponding dictionary view (segments,
        entities, relations, attributes)
        according to the annotation category (TextBoundAnnotation, Entity, Relation,
        Attribute).

        Note that entity is also considered as a segment of the text.

        Parameters
        ----------
        annotation : Annotation
            Annotation to add.

        Raises
        ------
        ValueError
            If `annotation.id` is already in Document.annotations.
        """
        try:
            super().add_annotation(annotation)
        except ValueError as err:
            raise err

        if isinstance(annotation, TextBoundAnnotation):
            if annotation.label not in self.segments.keys():
                self.segments[annotation.label] = [annotation.id]
            else:
                self.segments[annotation.label].append(annotation.id)

        if isinstance(annotation, Entity):
            if annotation.label not in self.entities.keys():
                self.entities[annotation.label] = [annotation.id]
            else:
                self.entities[annotation.label].append(annotation.id)
        elif isinstance(annotation, Relation):
            pass  # TODO: complete when key is determined
        elif isinstance(annotation, Attribute):
            if annotation.target_id not in self.attributes.keys():
                self.attributes[annotation.target_id] = [annotation.id]
            else:
                self.attributes[annotation.target_id].append(annotation.id)

    def get_attributes_by_annotation(self, ann_id):
        res = dict()
        for attr_id in self.attributes.get(ann_id):
            attribute = self.get_annotation_by_id(attr_id)
            res[attribute.label] = attribute
        return res
