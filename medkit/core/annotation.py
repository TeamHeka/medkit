__all__ = ["Annotation"]

import abc
import uuid

from typing import Dict


class Annotation(abc.ABC):
    def __init__(
        self, origin_id: str, label: str, ann_id: str = None, metadata: Dict = None
    ):
        """
        Provide common initialization for annotation instances

        Parameters
        ----------
        origin_id: str
            The id of the operation which creates annotation
            (i.e., ProcessingDescription.id)
        label: str
            The annotation label
        ann_id: str, Optional
            The annotation id
        metadata: dict
            The dictionary containing the annotation metadata
        """
        if ann_id:
            self.id = ann_id
        else:
            self.id = str(uuid.uuid1())
        self.origin_id = origin_id
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
