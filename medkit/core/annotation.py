__all__ = ["Annotation"]

import abc
import uuid


class Annotation(abc.ABC):
    @abc.abstractmethod
    def __init__(self, origin, label: str):
        self.id = uuid.uuid1()
        self.origin = origin
        self.label = label

    @abc.abstractmethod
    def __repr__(self):
        return f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r}"
