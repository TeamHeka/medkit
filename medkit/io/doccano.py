import abc
import dataclasses
from typing import Any, Dict, List, Tuple
from typing_extensions import Self
from medkit.core.attribute import Attribute

from medkit.core.text import Entity, Relation, Span, TextDocument, Segment
from medkit.core.text.span_utils import normalize_spans

DEFAULT_SEQUENCE_SOURCE_LABEL = "DOCCANO_SOURCE"
DEFAULT_SEQUENCE_LABEL = "DOCCANO_SEQUENCE"
DEFAULT_DOCCANO_LABEL = "DOCCANO_LABEL"

DEFAULT_COLUMN_DATA = "text"
DEFAULT_COLUMN_LABEL = "label"


@dataclasses.dataclass()
class DoccanoEntity:
    id: int
    start_offset: int
    end_offset: int
    label: str

    @classmethod
    def from_medkit(cls, entity: Entity) -> Self:
        uid = entity.metadata.get("doccano_id", entity.uid)
        spans = normalize_spans(entity.spans)
        return cls(
            id=uid,
            label=entity.label,
            start_offset=spans[0].start,
            end_offset=spans[-1].end,
        )

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            id=self.id,
            label=self.label,
            start_offset=self.start_offset,
            end_offset=self.end_offset,
        )


@dataclasses.dataclass()
class DoccanoEntityTuple:
    start_offset: int
    end_offset: int
    label: str


@dataclasses.dataclass()
class DoccanoRelation:
    id: int
    from_id: int
    to_id: int
    type: str


@dataclasses.dataclass()
class DoccanoDoc(abc.ABC):
    text: str

    @abc.abstractmethod
    def from_dict(cls, doc_line: Dict[str, Any]) -> Self:
        raise NotImplementedError

    @abc.abstractmethod
    def to_medkit(self) -> Any:
        raise NotImplementedError


@dataclasses.dataclass()
class DoccanoDocRelationExtraction(DoccanoDoc):
    id: int
    entities: Dict[str, DoccanoEntity]
    relations: Dict[str, DoccanoRelation]
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(cls, doc_line: Dict[str, Any]) -> Self:
        id = doc_line.get("id", None)
        text = doc_line[DEFAULT_COLUMN_DATA]
        metadata = doc_line.get("metadata", {})
        entities = dict()
        relations = dict()

        for ann in doc_line["entities"]:
            entity = DoccanoEntity(**ann)
            entities[entity.id] = entity

        for ann in doc_line["relations"]:
            relation = DoccanoRelation(**ann)
            relations[relation.id] = relation

        return cls(
            text=text, id=id, entities=entities, relations=relations, metadata=metadata
        )

    def to_medkit(self) -> TextDocument:
        anns_by_doccano_id = dict()
        for doccano_entity in self.entities.values():
            text = self.text[doccano_entity.start_offset : doccano_entity.end_offset]
            entity = Entity(
                text=text,
                label=doccano_entity.label,
                spans=[Span(doccano_entity.start_offset, doccano_entity.end_offset)],
                metadata=dict(doccano_id=doccano_entity.id),
            )
            anns_by_doccano_id[doccano_entity.id] = entity

        for doccano_relation in self.relations.values():
            relation = Relation(
                label=doccano_relation.type,
                source_id=anns_by_doccano_id[doccano_relation.from_id].uid,
                target_id=anns_by_doccano_id[doccano_relation.to_id].uid,
                metadata=dict(doccano_id=doccano_relation.id),
            )
            anns_by_doccano_id[doccano_relation.id] = relation

        metadata = self.metadata.copy().update(dict(doccano_id=self.id))
        doc = TextDocument(
            text=self.text, anns=list(anns_by_doccano_id.values()), metadata=metadata
        )
        return doc


@dataclasses.dataclass()
class DoccanoDocSeqLabeling(DoccanoDoc):
    entities: List[DoccanoEntityTuple]
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(cls, doc_line: Dict[str, Any]) -> Self:
        text = doc_line[DEFAULT_COLUMN_DATA]
        metadata = doc_line.get("metadata", {})
        entities = [DoccanoEntityTuple(*ann) for ann in doc_line[DEFAULT_COLUMN_LABEL]]
        return cls(text=text, label=entities, metadata=metadata)

    def to_medkit(self) -> TextDocument:
        doc = TextDocument(text=self.text, metadata=self.metadata)
        for doccano_entity in self.entities:
            text = self.text[doccano_entity.start_offset : doccano_entity.end_offset]
            doc.anns.add(
                Entity(
                    text=text,
                    label=doccano_entity.label,
                    spans=[
                        Span(doccano_entity.start_offset, doccano_entity.end_offset)
                    ],
                )
            )

        return doc


@dataclasses.dataclass()
class DoccanoDocSeq2Seq(DoccanoDoc):
    sequences: List[str]

    @classmethod
    def from_dict(cls, doc_line: Dict[str, Any]) -> Self:
        text = doc_line[DEFAULT_COLUMN_DATA]
        sequences = [seq for seq in doc_line[DEFAULT_COLUMN_LABEL]]
        return cls(text=text, sequences=sequences)

    def to_medkit(self) -> Tuple[Segment, List[Segment]]:
        source = Segment(
            text=self.text,
            spans=[Span(0, len(self.text))],
            label=DEFAULT_SEQUENCE_SOURCE_LABEL,
        )
        sequences = [
            Segment(
                text=seq_text,
                spans=[Span(0, len(seq_text))],
                label=DEFAULT_SEQUENCE_LABEL,
            )
            for seq_text in self.sequences
        ]
        return (source, sequences)


@dataclasses.dataclass()
class DoccanoDocTextClassification(DoccanoDoc):
    label: str

    @classmethod
    def from_dict(cls, doc_line: Dict[str, Any]) -> Self:
        text = doc_line[DEFAULT_COLUMN_DATA]
        return cls(text=text, label=doc_line[DEFAULT_COLUMN_LABEL][0])

    def to_medkit(self) -> TextDocument:
        doc = TextDocument(text=self.text)
        doc.raw_segment.attrs.add(
            Attribute(label=DEFAULT_DOCCANO_LABEL, value=self.label)
        )
        return doc
