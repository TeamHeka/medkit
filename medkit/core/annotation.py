from __future__ import annotations

__all__ = ["Annotation", "Attribute"]

import abc
from typing import Any, Dict, List, Optional

from medkit.core.id import generate_id


class Annotation(abc.ABC):
    def __init__(
        self,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        ann_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Provide common initialization for annotation instances

        Parameters
        ----------
        label: str
            The annotation label
        attrs:
            The attributes of the annotation
        ann_id: str, Optional
            The annotation id
        metadata: dict
            The dictionary containing the annotation metadata
        """
        if ann_id is None:
            ann_id = generate_id()
        if attrs is None:
            attrs = []
        if metadata is None:
            metadata = {}

        self.id: str = ann_id
        self.label: str = label
        self.attrs: List[Attribute] = attrs
        self.metadata: Dict[str, Any] = metadata

    def add_metadata(self, key: str, value: Any):
        if key in self.metadata.keys():
            raise ValueError(f"Metadata key {key} is already used")
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        attrs = [a.to_dict() for a in self.attrs]
        return dict(id=self.id, label=self.label, attrs=attrs, metadata=self.metadata)

    def __repr__(self):
        return (
            f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r},"
            f" nb_attrs={len(self.attrs)}"
        )


class Attribute:
    def __init__(
        self,
        label: str,
        value: Optional[Any] = None,
        attr_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a medkit attribute, to be added to an annotation

        Parameters
        ----------
        label: str
            The attribute label
        value: str, Optional
            The value of the attribute
        attr_id: str, Optional
            The id of the attribute (if existing)
        metadata: Dict[str, Any], Optional
            The metadata of the attribute
        """
        if attr_id is None:
            attr_id = generate_id()
        if metadata is None:
            metadata = {}

        self.id: str = attr_id
        self.label: str = label
        self.value: Optional[Any] = value
        self.metadata: Dict[str, Any] = metadata

    def add_metadata(self, key: str, value: Any):
        if key in self.metadata.keys():
            raise ValueError(f"Metadata key {key} is already used")
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            id=self.id, label=self.label, value=self.value, metadata=self.metadata
        )

    def __repr__(self):
        return (
            f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r},"
            f" value={self.value}"
        )
