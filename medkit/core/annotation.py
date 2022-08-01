from __future__ import annotations

__all__ = ["Annotation", "Attribute"]

import abc
from typing import Any, Dict, List, Set, Optional

from medkit.core.id import generate_id


class Annotation(abc.ABC):
    def __init__(
        self,
        label: str,
        keys: Optional[Set[str]] = None,
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
        keys: Set[str], Optional
            The set of pipeline output keys which annotation belongs to
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
        self.keys: Set[str] = keys if keys is not None else set()
        self.metadata: Dict[str, Any] = metadata

        self._attrs_by_id: Dict[str, Attribute] = {}
        self._attr_ids_by_label: Dict[str, List[str]] = {}
        for attr in attrs:
            self.add_attr(attr)

    def add_attr(self, attr: Attribute):
        """
        Attach an attribute to the annotation.

        Parameters
        ----------
        attr:
            Attribute to add.

        Raises
        ------
        ValueError
            If the attribute is already attached to the annotation
            (based on `attr.id`).
        """
        id = attr.id
        if id in self._attrs_by_id:
            raise ValueError(f"Attribute with id {id} already attached to annotation")

        # TODO: we should probably store attributes in a Store,
        # the same way annotations in a document are stored in a Store because:
        # - ProvBuilder already adds attributes to the store
        # - an attribute can be shared among several annotations
        self._attrs_by_id[id] = attr

        label = attr.label
        if label not in self._attr_ids_by_label:
            self._attr_ids_by_label[label] = []
        self._attr_ids_by_label[label].append(id)

    def get_attrs(self) -> List[Attribute]:
        """
        Return the attributes of the annotation.

        Returns
        -------
        List[Attribute]
            List of all the attributes attached to the annotation.
        """
        return list(self._attrs_by_id.values())

    def get_attrs_by_label(self, label: str) -> List[Attribute]:
        """
        Return the attributes of the annotation having a specific label.

        Returns
        -------
        List[Attribute]
            List of all the attributes attached to the annotation
            with labels equal to `label`.
        """

        return [self._attrs_by_id[id] for id in self._attr_ids_by_label.get(label, [])]

    def add_key(self, key: str):
        self.keys.add(key)

    def keep_keys(self, keys):
        self.keys.intersection_update(keys)

    def add_metadata(self, key: str, value: Any):
        if key in self.metadata.keys():
            raise ValueError(f"Metadata key {key} is already used")
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        attrs = [a.to_dict() for a in self._attrs_by_id.values()]
        return dict(
            id=self.id,
            keys=list(self.keys),
            label=self.label,
            attrs=attrs,
            metadata=self.metadata,
        )

    def __repr__(self):
        return str(self.to_dict())


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
