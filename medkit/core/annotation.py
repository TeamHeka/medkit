__all__ = ["Annotation"]

import abc
import uuid

from typing import Dict


class Annotation(abc.ABC):
    def __init__(
        self, origin: str, label: str, ann_id: str = None, metadata: Dict = None
    ):
        if ann_id:
            self.id = ann_id
        else:
            self.id = str(uuid.uuid1())
        self.origin = origin
        self.label = label
        self.metadata = metadata

    def add_metadata(self, key, value):
        if self.metadata is None:
            self.metadata = {}
        if key in self.metadata.keys():
            raise ValueError(f"Metadata key {key} is already used")
        self.metadata[key] = value

    @abc.abstractmethod
    def __repr__(self):
        return f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r}"
