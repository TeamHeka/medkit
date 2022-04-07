from __future__ import annotations

__all__ = ["TextDocument"]

import random
from typing import Any, Dict, List, Optional
import uuid

from medkit.core.document import Document
from medkit.core.store import Store
from medkit.core.text.annotation import TextAnnotation, Segment, Entity, Relation
from medkit.core.text.span import Span


class TextDocument(Document[TextAnnotation]):
    """Document holding text annotations

    Annotations must be subclasses of `TextAnnotation`."""

    RAW_TEXT_LABEL = "RAW_TEXT"

    def __init__(
        self,
        doc_id: Optional[str] = None,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        """
        Initializes the text document

        The method uses the abstract class Document to initialize a part
        and creates dictionary views for accessing entities and relations.

        Parameters
        ----------
        doc_id: str, Optional
            Document identifier. If None, an uuid is generated.
        text: str, Optional
            Document text
        metadata: dict  # TODO
            Document metadata
        store:
            Store to use for annotations
        """
        super().__init__(doc_id=doc_id, metadata=metadata, store=store)
        self.text: Optional[str] = text
        self.segments: Dict[str, List[str]] = dict()  # Key: label
        self.entities: Dict[str, List[str]] = dict()  # Key: label
        self.relations: Dict[str, List[str]] = dict()  # Key: TODO : determine the key

        # auto-generated RAW_TEXT segment
        # not stored with other annotations but injected in calls to get_annotations_by_label()
        # and get_annotation_by_id()
        self._raw_text_seg: Optional[Segment] = self._gen_raw_text_segment()

    def add_annotation(self, annotation: TextAnnotation):
        """
        Add the annotation to this document

        The method uses the abstract class method to add the annotation
        in the Document.
        It also adds the annotation id to the corresponding dictionary view (segments,
        entities, relations)
        according to the annotation category (Segment, Entity, Relation).

        Note that entity is also considered as a segment of the text.

        Parameters
        ----------
        annotation:
            Annotation to add.

        Raises
        ------
        ValueError
            If `annotation.id` is already in Document.annotations.
        """
        if annotation.label == self.RAW_TEXT_LABEL:
            raise RuntimeError(
                f"Cannot add annotation with reserved label {self.RAW_TEXT_LABEL}"
            )

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

    def get_annotations_by_label(self, label) -> List[TextAnnotation]:
        # inject RAW_TEXT segment
        if self._raw_text_seg is not None and label == self.RAW_TEXT_LABEL:
            return [self._raw_text_seg]
        return super().get_annotations_by_label(label)

    def get_annotation_by_id(self, annotation_id) -> Optional[TextAnnotation]:
        # inject RAW_TEXT segment
        if self._raw_text_seg is not None and annotation_id == self._raw_text_seg.id:
            return self._raw_text_seg
        return super().get_annotation_by_id(annotation_id)

    def _gen_raw_text_segment(self) -> Optional[Segment]:
        if self.text is None:
            return None

        # generate deterministic uuid based on document id
        # so that the annotation id is the same if the doc id is the same
        rng = random.Random(self.id)
        id = str(uuid.UUID(int=rng.getrandbits(128)))

        return Segment(
            label=self.RAW_TEXT_LABEL,
            spans=[Span(0, len(self.text))],
            text=self.text,
            ann_id=id,
        )

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(text=self.text)
        return data
