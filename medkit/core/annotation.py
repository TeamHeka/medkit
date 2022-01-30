__all__ = ["Annotation"]

import abc
import uuid


class Annotation(abc.ABC):
    @abc.abstractmethod
    def __init__(self, ann_source, label: str):
        self.id = uuid.uuid1()
        self.ann_source = ann_source
        self.label = label

    @abc.abstractmethod
    def __repr__(self):
        return f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r}"
