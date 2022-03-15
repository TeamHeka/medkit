from __future__ import annotations

__all__ = [
    "InputConverter",
    "OutputConverter",
    "ProcessingDescription",
    "RuleBasedAnnotator",
]

import abc
import dataclasses
from typing import Any, Dict, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from medkit.core.document import Collection


@dataclasses.dataclass
class ProcessingDescription:
    """Description of a specific instance of a processing module.

    Parameters
    ----------
    name:
        The name of the processing module (typically the class name)
    id:
        A unique identifier for the instance
    config:
        The specific configuration of the instance. Ideally, it
        should be possible to use that dict to reinstantiate the same
        processing module.
    """

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
