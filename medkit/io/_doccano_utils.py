import dataclasses
from typing import Any, Dict, List, Tuple

from typing_extensions import Self


@dataclasses.dataclass()
class DoccanoEntity:
    id: int
    start_offset: int
    end_offset: int
    label: str

    def to_dict(self) -> Dict[str, Any]:
        entity_dict = dict(
            id=self.id,
            start_offset=self.start_offset,
            end_offset=self.end_offset,
            label=self.label,
        )
        return entity_dict


@dataclasses.dataclass()
class DoccanoEntityTuple:
    start_offset: int
    end_offset: int
    label: str

    def to_tuple(self) -> Tuple[Any]:
        return (self.start_offset, self.end_offset, self.label)


@dataclasses.dataclass()
class DoccanoRelation:
    id: int
    from_id: int
    to_id: int
    type: str

    def to_dict(self) -> Dict[str, Any]:
        relation_dict = dict(
            id=self.id,
            from_id=self.from_id,
            to_id=self.to_id,
            type=self.type,
        )
        return relation_dict


@dataclasses.dataclass()
class DoccanoDocRelationExtraction:
    id: int
    text: str
    entities: List[DoccanoEntity]
    relations: List[DoccanoRelation]
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(cls, doc_line: Dict[str, Any], column_text: str) -> Self:
        id = doc_line.get("id", None)
        text = doc_line[column_text]
        metadata = doc_line.get("metadata", {})
        entities = [DoccanoEntity(**ann) for ann in doc_line["entities"]]
        relations = [DoccanoRelation(**ann) for ann in doc_line["relations"]]
        return cls(
            text=text, id=id, entities=entities, relations=relations, metadata=metadata
        )

    def to_dict(self) -> Dict[str, Any]:
        doc_dict = dict(
            id=self.id,
            text=self.text,
        )

        doc_dict["entities"] = [ent.to_dict() for ent in self.entities]
        doc_dict["relations"] = [rel.to_dict() for rel in self.relations]

        if self.metadata:
            doc_dict["metadata"] = self.metadata
        return doc_dict


@dataclasses.dataclass()
class DoccanoDocSeqLabeling:
    text: str
    entities: List[DoccanoEntityTuple]
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(
        cls, doc_line: Dict[str, Any], column_text: str, column_label: str
    ) -> Self:
        text = doc_line[column_text]
        metadata = doc_line.get("metadata", {})
        entities = [DoccanoEntityTuple(*ann) for ann in doc_line[column_label]]
        return cls(text=text, entities=entities, metadata=metadata)

    def to_dict(self) -> Dict[str, Any]:
        doc_dict = dict(text=self.text)
        doc_dict["label"] = [ent.to_tuple() for ent in self.entities]

        if self.metadata:
            doc_dict["metadata"] = self.metadata
        return doc_dict


@dataclasses.dataclass()
class DoccanoDocTextClassification:
    text: str
    label: str
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(
        cls, doc_line: Dict[str, Any], column_text: str, column_label: str
    ) -> Self:
        text = doc_line[column_text]
        metadata = doc_line.get("metadata", {})
        return cls(text=text, label=doc_line[column_label][0], metadata=metadata)

    def to_dict(self) -> Dict[str, Any]:
        doc_dict = dict(text=self.text, label=[str(self.label)])
        if self.metadata:
            doc_dict["metadata"] = self.metadata
        return doc_dict
