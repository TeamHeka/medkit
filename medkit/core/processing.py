__all__ = ["InputConverter", "OutputConverter", "ProcessingDescription"]

import abc
import dataclasses
import uuid

from typing import Dict

from medkit.core.document import Collection


@dataclasses.dataclass
class ProcessingDescription:
    name: str
    id: str = str(uuid.uuid1())
    config: Dict[str, str] = None


class InputConverter(abc.ABC):

    @property
    @abc.abstractmethod
    def description(self):
        pass

    @abc.abstractmethod
    def __init__(self, config=None):
        pass

    @abc.abstractmethod
    def load(self, **kwargs) -> Collection:
        pass


class OutputConverter(abc.ABC):

    @property
    @abc.abstractmethod
    def description(self):
        pass

    @abc.abstractmethod
    def __init__(self, config=None):
        pass

    @abc.abstractmethod
    def save(self, collection):
        pass
