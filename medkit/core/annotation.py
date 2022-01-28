__all__ = ["Annotation"]

import abc
import uuid


class Annotation(abc.ABC):
    @abc.abstractmethod
    def __init__(self, label):
        self.id = uuid.uuid1()
        self.label = label
        # TODO: add source of the annotation

    @abc.abstractmethod
    def __repr__(self):
        return f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r}"
