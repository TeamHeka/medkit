__all__ = ["Converter"]

import abc
import uuid

from medkit.core import Collection


class AnnotationSource(abc.ABC):
    def __init__(self, config=None):
        self.id = uuid.uuid1()
        self.name = self.__class__.__name__
        self.config = config


class Converter(AnnotationSource):
    def __init__(self, config=None):
        super().__init__(config)

    @abc.abstractmethod
    def load(self, **kwargs):
        collection = Collection()
        return collection

    @abc.abstractmethod
    def save(self, collection):
        pass
