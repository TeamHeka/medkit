from __future__ import annotations

__all__ = ["Annotation"]

import abc
from typing import Any, Dict, List, Set, Optional

from medkit.core.attribute import Attribute
from medkit.core.attribute_container import AttributeContainer
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

        self.attrs = AttributeContainer(store=store)
        for attr in attrs:
            self.attrs.add(attr)

    def add_key(self, key: str):
        self.keys.add(key)

    def keep_keys(self, keys):
        self.keys.intersection_update(keys)

    def to_dict(self) -> Dict[str, Any]:
        attrs = [a.to_dict() for a in self.attrs]
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
