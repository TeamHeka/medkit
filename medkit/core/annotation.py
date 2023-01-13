from __future__ import annotations

__all__ = ["Annotation"]

import abc
from typing import Any, Dict, List, Set, Optional

from medkit.core.attribute import Attribute
from medkit.core.id import generate_id
from medkit.core.store import Store, DictStore


class Annotation(abc.ABC):
    def __init__(
        self,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        uid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        """
        Provide common initialization for annotation instances

        Parameters
        ----------
        label: str
            The annotation label
        attrs:
            The attributes of the annotation
        uid: str, Optional
            The annotation identifier
        metadata: dict
            The dictionary containing the annotation metadata
        store:
            Optional shared store to hold the attributes. If none provided,
            an internal store will be used.
        """
        if uid is None:
            uid = generate_id()
        if attrs is None:
            attrs = []
        if metadata is None:
            metadata = {}
        if store is None:
            store = DictStore()

        self.uid: str = uid
        self.label: str = label
        self.keys: Set[str] = set()
        self.metadata: Dict[str, Any] = metadata
        self.store = store

        self._attrs_id: List[str] = []
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
            (based on `attr.uid`).
        """
        uid = attr.uid
        if attr.uid in self._attrs_id:
            raise ValueError(f"Attribute with uid {uid} already attached to annotation")

        self._attrs_id.append(uid)
        self.store.store_data_item(attr)

        label = attr.label
        if label not in self._attr_ids_by_label:
            self._attr_ids_by_label[label] = []
        self._attr_ids_by_label[label].append(uid)

    def get_attrs(self) -> List[Attribute]:
        """
        Return the attributes of the annotation.

        Returns
        -------
        List[Attribute]
            List of all the attributes attached to the annotation.
        """
        return [self.store.get_data_item(uid) for uid in self._attrs_id]

    def get_attrs_by_label(self, label: str) -> List[Attribute]:
        """
        Return the attributes of the annotation having a specific label.

        Returns
        -------
        List[Attribute]
            List of all the attributes attached to the annotation
            with labels equal to `label`.
        """

        return [
            self.store.get_data_item(uid)
            for uid in self._attr_ids_by_label.get(label, [])
        ]

    def add_key(self, key: str):
        self.keys.add(key)

    def keep_keys(self, keys):
        self.keys.intersection_update(keys)

    def to_dict(self) -> Dict[str, Any]:
        attrs = [a.to_dict() for a in self._attrs_by_id.values()]
        return dict(
            uid=self.uid,
            label=self.label,
            attrs=attrs,
            metadata=self.metadata,
            class_name=self.__class__.__name__,
        )

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, annotation_dict: Dict[str, Any]) -> Annotation:
        raise NotImplementedError

    def __repr__(self):
        return str(self.to_dict())
