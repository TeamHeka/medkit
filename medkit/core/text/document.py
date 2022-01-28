__all__ = ["TextDocument"]

from medkit.core import Document, Annotation
from medkit.core.text import Entity, Relation, Attribute


class TextDocument(Document):
    def __init__(self, text, metadata=None):
        """
        Initializes the text document

        The method uses the abstract class Document to initialize a part
        and creates dictionary views for accessing entities, attributes and
        relations.

        Parameters
        ----------
        text: str
            Document text
        metadata: TODO

        """
        super().__init__(metadata)
        self.text = text
        self.entities = dict()  # Key: label
        self.relations = dict()  # Key: TODO : determine the key
        self.attributes = dict()  # Key : target_id

    def add_annotation(self, annotation: Annotation):
        """
        Add the annotation to this document

        The method uses the abstract class method to add the annotation
        in the Document.
        It also adds the annotation id to the corresponding dictionary view
        according to the annotation category (Entity, Relation, Attribute)

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
