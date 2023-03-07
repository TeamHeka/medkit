from __future__ import annotations

__all__ = ["TextAnnotation", "Segment", "Entity", "Relation"]

import abc
import dataclasses
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TYPE_CHECKING,
)
from typing_extensions import Self

from medkit.core.attribute import Attribute
from medkit.core.attribute_container import AttributeContainer
from medkit.core import dict_conv
from medkit.core.id import generate_id
from medkit.core.store import Store
from medkit.core.text.normalization import EntityNormalization
from medkit.core.text.span import AnySpan
import medkit.core.text.span_utils as span_utils

if TYPE_CHECKING:
    from medkit.core.text.document import TextDocument


@dataclasses.dataclass(init=False)
class TextAnnotation(abc.ABC):
    """Base abstract class for all text annotations

    Attributes
    ----------
    uid:
        Unique identifier of the annotation.
    label:
        The label for this annotation (e.g., SENTENCE)
    attrs:
        Attributes of the annotation. Stored in a
        :class:{~medkit.core.AttributeContainer} but can be passed as a list at
        init.
    metadata:
        The metadata of the annotation
    keys:
        Pipeline output keys to which the annotation belongs to.
    """

    uid: str
    label: str
    attrs: AttributeContainer
    metadata: Dict[str, Any]
    keys: Set[str]

    @abc.abstractmethod
    def __init__(
        self,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        if attrs is None:
            attrs = []
        if metadata is None:
            metadata = {}
        if uid is None:
            uid = generate_id()

        self.uid = uid
        self.label = label
        self.metadata = metadata
        self.keys = set()

        self.attrs = AttributeContainer(ann_id=self.uid)
        for attr in attrs:
            self.attrs.add(attr)

    def __init_subclass__(cls):
        super().__init_subclass__()
        # type-annotated intermediary variable needed to keep mypy happy
        parent_class: Type = TextAnnotation
        dict_conv.register_subclass(parent_class, cls)

    @staticmethod
    def from_dict(ann_dict: Dict[str, Any]) -> TextAnnotation:
        subclass = dict_conv.get_subclass_for_data_dict(TextAnnotation, ann_dict)
        return subclass.from_dict(ann_dict)

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError()


@dataclasses.dataclass(init=False)
class Segment(TextAnnotation):
    """
    Text segment referencing part of an {class}`~medkit.core.text.TextDocument`.

    Attributes
    ----------
    uid:
        The segment identifier.
    label:
        The label for this segment (e.g., SENTENCE)
    text:
        Text of the segment.
    spans:
        List of spans indicating which parts of the segment text correspond to
        which part of the document's full text.
    attrs:
        Attributes of the segment. Stored in a
        :class:{~medkit.core.AttributeContainer} but can be passed as a list at
        init.
    metadata:
        The metadata of the segment
    keys:
        Pipeline output keys to which the segment belongs to.
    """

    spans: List[AnySpan]
    text: str

    def __init__(
        self,
        label: str,
        text: str,
        spans: List[AnySpan],
        attrs: Optional[List[Attribute]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
        store: Optional[Store] = None,
    ):
        super().__init__(label=label, attrs=attrs, metadata=metadata, uid=uid)

        self.text = text
        self.spans = spans

    def to_dict(self) -> Dict[str, Any]:
        spans = [s.to_dict() for s in self.spans]
        attrs = [a.to_dict() for a in self.attrs]
        segment_dict = dict(
            uid=self.uid,
            label=self.label,
            text=self.text,
            spans=spans,
            attrs=attrs,
            metadata=self.metadata,
        )
        dict_conv.add_class_name_to_data_dict(self, segment_dict)
        return segment_dict

    @classmethod
    def from_dict(cls, segment_dict: Dict[str, Any]) -> Self:
        """
        Creates a Segment from a dict

        Parameters
        ----------
        segment_dict: dict
            A dictionary from a serialized segment as generated by to_dict()
        """

        dict_conv.check_class_matches_data_dict(cls, segment_dict)

        spans = [AnySpan.from_dict(s) for s in segment_dict["spans"]]
        attrs = [Attribute.from_dict(a) for a in segment_dict["attrs"]]
        return cls(
            uid=segment_dict["uid"],
            label=segment_dict["label"],
            text=segment_dict["text"],
            spans=spans,
            attrs=attrs,
            metadata=segment_dict["metadata"],
        )

    def get_snippet(self, doc: TextDocument, max_extend_length: int) -> str:
        """Return a portion of the original text containing the annotation

        Parameters
        ----------
        doc:
            The document to which the annotation is attached

        max_extend_length:
            Maximum number of characters to use around the annotation

        Returns
        -------
        str:
            A portion of the text around the annotation
        """
        spans_normalized = span_utils.normalize_spans(self.spans)
        start = min(s.start for s in spans_normalized)
        end = max(s.end for s in spans_normalized)
        start_extended = max(start - max_extend_length // 2, 0)
        remaining_max_extend_length = max_extend_length - (start - start_extended)
        end_extended = min(end + remaining_max_extend_length, len(doc.text))
        return doc.text[start_extended:end_extended]


@dataclasses.dataclass(init=False)
class Entity(Segment):
    """
    Text entity referencing part of an {class}`~medkit.core.text.TextDocument`.

    Attributes
    ----------
    uid:
        The entity identifier.
    label:
        The label for this entity (e.g., DISEASE)
    text:
        Text of the entity.
    spans:
        List of spans indicating which parts of the entity text correspond to
        which part of the document's full text.
    attrs:
        Attributes of the entity. Stored in a
        :class:{~medkit.core.AttributeContainer} but can be passed as a list at
        init.
    metadata:
        The metadata of the entity
    keys:
        Pipeline output keys to which the entity belongs to.
    """

    NORM_LABEL: ClassVar[str] = "NORMALIZATION"
    """
    Label to use for normalization attributes
    """

    def add_norm(self, normalization: EntityNormalization) -> Attribute:
        """
        Attach an :class:`~medkit.core.text.normalization.EntityNormalization`
        object to the entity.

        This helper will wrap `normalization` in an
        :class:`~medkit.core.annotation.Attribute` with
        :attr:`Entity.NORM_LABEL` as label and add it to the entity.

        Returns
        -------
        Attribute:
            The attribute that was created and added to the entity
        """

        attr = Attribute(label=self.NORM_LABEL, value=normalization)
        self.attrs.add(attr)
        return attr

    def get_norms(self) -> List[EntityNormalization]:
        """
        Return all :class:`~medkit.core.text.normalization.EntityNormalization`
        objects attached to the entity.

        This helper will retrieve all the entity attributes with
        :attr:`Entity.NORM_LABEL` as label and return their
        :class:`~medkit.core.text.normalization.EntityNormalization` values.

        Returns
        -------
        List[EntityNormalization]:
            All normalizations attached to the entity.
        """
        return [a.value for a in self.attrs.get(label=self.NORM_LABEL)]


@dataclasses.dataclass(init=False)
class Relation(TextAnnotation):
    """
    Relation between two text entities.

    Attributes
    ----------
    uid:
        The identifier of the relation
    label:
        The relation label
    source_id:
        The identifier of the entity from which the relation is defined
    target_id:
        The identifier of the entity to which the relation is defined
    attrs:
        The attributes of the relation
    metadata:
        The metadata of the relation
    keys:
        Pipeline output keys to which the relation belongs to
    """

    source_id: str
    target_id: str

    def __init__(
        self,
        label: str,
        source_id: str,
        target_id: str,
        attrs: Optional[List[Attribute]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
        store: Optional[Store] = None,
    ):
        super().__init__(label=label, attrs=attrs, metadata=metadata, uid=uid)

        self.source_id = source_id
        self.target_id = target_id

    def to_dict(self) -> Dict[str, Any]:
        attrs = [a.to_dict() for a in self.attrs]
        relation_dict = dict(
            uid=self.uid,
            label=self.label,
            source_id=self.source_id,
            target_id=self.target_id,
            attrs=attrs,
            metadata=self.metadata,
        )
        dict_conv.add_class_name_to_data_dict(self, relation_dict)
        return relation_dict

    @classmethod
    def from_dict(cls, relation_dict: Dict[str, Any]) -> Self:
        """
        Creates a Relation from a dict

        Parameters
        ----------
        relation_dict: dict
            A dictionary from a serialized relation as generated by to_dict()
        """

        dict_conv.check_class_matches_data_dict(cls, relation_dict)

        attrs = [Attribute.from_dict(a) for a in relation_dict["attrs"]]
        return cls(
            uid=relation_dict["uid"],
            label=relation_dict["label"],
            source_id=relation_dict["source_id"],
            target_id=relation_dict["target_id"],
            attrs=attrs,
            metadata=relation_dict["metadata"],
        )
