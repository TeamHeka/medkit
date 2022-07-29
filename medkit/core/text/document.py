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

    Annotations must be subclasses of `TextAnnotation`.

    """

    RAW_LABEL = "RAW_TEXT"
    """Label to be used for raw text
    """

    def __init__(
        self,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
        doc_id: Optional[str] = None,
    ):
        """
        Initializes the text document

        The method uses the abstract class Document to initialize a part
        and creates dictionary views for accessing entities and relations.

        Parameters
        ----------
        text: str, Optional
            Document text
        metadata: dict  # TODO
            Document metadata
        store:
            Store to use for annotations
        doc_id: str, Optional
            Document identifier. If None, an uuid is generated.

        Examples
        --------
        To get the raw text as an annotation to pass to processing operations:

        >>> doc = TextDocument(text="hello")
        >>> raw_text = doc.get_annotations_by_label(TextDocument.RAW_LABEL)[0]
        """
        super().__init__(doc_id=doc_id, metadata=metadata, store=store)
        self.text: Optional[str] = text
        self._segment_ids: List[str] = []
        self._entity_ids: List[str] = []
        self.relations_by_source: Dict[str, List[str]] = dict()  # Key: source_id

        # auto-generated raw segment
        # not stored with other annotations but injected in calls to get_annotations_by_label()
        # and get_annotation_by_id()
        self.raw_segment: Optional[Segment] = self._generate_raw_segment()

    def _generate_raw_segment(self) -> Optional[Segment]:
        if self.text is None:
            return None

        # generate deterministic uuid based on document id
        # so that the annotation id is the same if the doc id is the same
        rng = random.Random(self.id)
        id = str(uuid.UUID(int=rng.getrandbits(128)))

        return Segment(
            label=self.RAW_LABEL,
            spans=[Span(0, len(self.text))],
            text=self.text,
            ann_id=id,
        )

    def add_annotation(self, annotation: TextAnnotation):
        """
        Add the annotation to this document

        The method uses the abstract class method to add the annotation
        in the Document.
        It also adds the annotation id to the corresponding dictionary view (segments,
        entities, relations)
        according to the annotation category (Segment, Entity, Relation).

        Parameters
        ----------
        annotation:
            Annotation to add.

        Raises
        ------
        ValueError
            If `annotation.id` is already in Document.annotations.


        """
        if annotation.label == self.RAW_LABEL:
            raise RuntimeError(
                f"Cannot add annotation with reserved label {self.RAW_LABEL}"
            )

        try:
            super().add_annotation(annotation)
        except ValueError as err:
            raise err

        if isinstance(annotation, Entity):
            self._entity_ids.append(annotation.id)
        elif isinstance(annotation, Segment):
            self._segment_ids.append(annotation.id)
        elif isinstance(annotation, Relation):
            if annotation.source_id not in self.relations_by_source:
                self.relations_by_source[annotation.source_id] = []
            self.relations_by_source[annotation.source_id].append(annotation.id)

    def get_annotations_by_label(self, label) -> List[TextAnnotation]:
        # inject raw segment
        if self.raw_segment is not None and label == self.RAW_LABEL:
            return [self.raw_segment]
        return super().get_annotations_by_label(label)

    def get_annotation_by_id(self, annotation_id) -> Optional[TextAnnotation]:
        # inject raw segment
        if self.raw_segment is not None and annotation_id == self.raw_segment.id:
            return self.raw_segment
        return super().get_annotation_by_id(annotation_id)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(text=self.text)
        return data

    def get_entities(self) -> List[Entity]:
        """Return all entities attached to document

        Returns
        -------
        List[Entity]:
            Entities in document
        """
        return [self.get_annotation_by_id(id) for id in self._entity_ids]

    def get_segments(self) -> List[Segment]:
        """Return all segments attached to document (not including entities)

        Returns
        -------
        List[Segment]:
            Segments in document
        """
        return [self.get_annotation_by_id(id) for id in self._segment_ids]

    def get_relations_by_source_id(self, source_ann_id) -> List[Relation]:
        relation_ids = self.relations_by_source.get(source_ann_id, [])
        relations = [self.store.get_data_item(id) for id in relation_ids]
        return relations

    def get_relations(self) -> List[Relation]:
        relations = [
            self.store.get_data_item(ann_id)
            for ids in self.relations_by_source.values()
            for ann_id in ids
        ]
        return relations
