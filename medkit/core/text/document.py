from __future__ import annotations

__all__ = ["TextDocument"]

import random
from typing import Dict, TYPE_CHECKING
import uuid

from medkit.core.annotation import Origin, Attribute
from medkit.core.document import Document
from medkit.core.text.annotation import Segment, Entity, Relation
from medkit.core.text.span import Span

if TYPE_CHECKING:
    from medkit.core.annotation import Annotation


class TextDocument(Document):

    RAW_TEXT_LABEL = "RAW_TEXT"

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

        if self.text is not None:
            raw_text_ann = self._gen_raw_text_annotation()
            self.add_annotation(raw_text_ann)

    def add_annotation(self, annotation: Annotation):
        """
        Add the annotation to this document

        The method uses the abstract class method to add the annotation
        in the Document.
        It also adds the annotation id to the corresponding dictionary view (segments,
        entities, relations, attributes)
        according to the annotation category (Segment, Entity, Relation,
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

        if isinstance(annotation, Segment):
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

    def get_attributes_by_annotation(self, ann_id: str) -> Dict[str, Attribute]:
        """
        Retrieve all attributes targeted onto an annotation.

        Parameters
        ----------
        ann_id
            The annotation id for which we want to get attributes.

        Returns
        -------
        Dict[str, List[Attribute]]
            A dictionary where key correspond to the Attribute label and
            where value is a list of Attribute instance having this label.
        """
        res = dict()
        for attr_id in self.attributes.get(ann_id, []):
            attribute = self.get_annotation_by_id(attr_id)
            if attribute.label not in res.keys():
                res[attribute.label] = []
            res[attribute.label].append(attribute)
        return res

    def _gen_raw_text_annotation(self):
        # generate deterministic uuid based on document id
        # so that the annotation id is the same if the doc id is the same
        rng = random.Random(self.id)
        id = str(uuid.UUID(int=rng.getrandbits(128)))

        return Segment(
            origin=Origin(),
            label=self.RAW_TEXT_LABEL,
            spans=[Span(0, len(self.text))],
            text=self.text,
            ann_id=id,
        )
