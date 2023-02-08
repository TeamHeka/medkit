from __future__ import annotations

__all__ = ["TextDocument"]

import random
from typing import Any, Dict, Optional
import uuid

from medkit.core.document import Document
from medkit.core.store import Store, DictStore
from medkit.core.text.annotation import TextAnnotation, Segment, Entity, Relation
from medkit.core.text.annotation_container import TextAnnotationContainer
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
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
        uid: Optional[str] = None,
    ):
        """
        Initializes the text document

        The method uses the abstract class Document to initialize a part
        and creates dictionary views for accessing entities and relations.

        Parameters
        ----------
        text:
            Document text
        metadata: dict  # TODO
            Document metadata
        store:
            Store to use for annotations
        uid: str, Optional
            Document identifier. If None, an uuid is generated.

        Examples
        --------
        To get the raw text as an annotation to pass to processing operations:

        >>> doc = TextDocument(text="hello")
        >>> raw_text = doc.anns.get(label=TextDocument.RAW_LABEL)[0]
        """

        if store is None:
            store = DictStore()
            has_shared_store = False
        else:
            has_shared_store = True

        self.uid: str = uid
        self.store: Store = store
        self.has_shared_store = has_shared_store

        # auto-generated raw segment to hold the text
        self.raw_segment: Segment = self._generate_raw_segment(text, self.uid)

        anns = TextAnnotationContainer(self.raw_segment, store)
        super().__init__(
            anns=anns,
            metadata=metadata,
            uid=uid,
        )

    @classmethod
    def _generate_raw_segment(cls, text: str, doc_id: str) -> Segment:
        # generate deterministic uuid based on document uid
        # so that the annotation uid is the same if the doc uid is the same
        rng = random.Random(doc_id)
        uid = str(uuid.UUID(int=rng.getrandbits(128)))

        return Segment(
            label=cls.RAW_LABEL,
            spans=[Span(0, len(text))],
            text=text,
            uid=uid,
        )

    @property
    def text(self) -> str:
        return self.raw_segment.text

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(text=self.text, class_name=self.__class__.__name__)
        return data

    @classmethod
    def from_dict(cls, doc_dict: Dict[str, Any]) -> TextDocument:
        """
        Creates a TextDocument from a dict

        Parameters
        ----------
        doc_dict: dict
            A dictionary from a serialized TextDocument as generated by to_dict()
        """
        anns = []
        for annotation_dict in doc_dict["anns"]:
            if annotation_dict["class_name"] == "Relation":
                anns.append(Relation.from_dict(annotation_dict))
            elif annotation_dict["class_name"] == "Segment":
                anns.append(Segment.from_dict(annotation_dict))
            elif annotation_dict["class_name"] == "Entity":
                anns.append(Entity.from_dict(annotation_dict))

        doc = cls(
            uid=doc_dict["uid"], metadata=doc_dict["metadata"], text=doc_dict["text"]
        )

        for ann in anns:
            doc.anns.add(ann)

        return doc
