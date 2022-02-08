from __future__ import annotations

__all__ = [
    "InputConverter",
    "OutputConverter",
    "ProcessingDescription",
    "RuleBasedAnnotator",
]

import abc
import dataclasses
import uuid

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from medkit.core.document import Collection


@dataclasses.dataclass
class ProcessingDescription:
    name: str
    id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid1()))
    config: Dict[str, Any] = None


class InputConverter(abc.ABC):
    @property
    @abc.abstractmethod
    def description(self) -> ProcessingDescription:
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
    def description(self) -> ProcessingDescription:
        pass

    @abc.abstractmethod
    def __init__(self, config=None):
        pass

    @abc.abstractmethod
    def save(self, collection):
        pass


class RuleBasedAnnotator(abc.ABC):
    @property
    @abc.abstractmethod
    def description(self) -> ProcessingDescription:
        pass

    @abc.abstractmethod
    def annotate(self, collection: Collection):
        pass
