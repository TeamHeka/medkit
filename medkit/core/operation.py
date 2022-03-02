from __future__ import annotations

__all__ = [
    "Operation",
    "OperationDescription",
    "ProcessingOperation",
    "RuleBasedAnnotator",
    "InputConverter",
    "OutputConverter",
]

import abc
import dataclasses
from typing import Any, Dict

from medkit.core.id import generate_id
from medkit.core.document import Collection


class Operation(abc.ABC):
    """Any medkit operation (io convertor, processing operation, etc)

    Parameters
    ----------
    description:
        Description of the operation
    """

    @property
    @abc.abstractmethod
    def description(self) -> OperationDescription:
        pass


@dataclasses.dataclass
class OperationDescription:
    """Description of a specific instance of an operation

    Parameters
    ----------
    name:
        The name of the operation (typically the class name)
    id:
        A unique identifier for the instance
    config:
        The specific configuration of the instance. Ideally, it
        should be possible to use that dict to reinstantiate the same
        operation
    """

    name: str
    id: str = dataclasses.field(default_factory=generate_id)
    config: Dict[str, Any] = None


class ProcessingOperation(Operation):
    """Operation that processes annotations"""

    pass


class RuleBasedAnnotator(ProcessingOperation):
    pass


class InputConverter(Operation):
    @abc.abstractmethod
    def __init__(self, config=None):
        pass

    @abc.abstractmethod
    def load(self, **kwargs) -> Collection:
        pass


class OutputConverter(Operation):
    @abc.abstractmethod
    def __init__(self, config=None):
        pass

    @abc.abstractmethod
    def save(self, collection: Collection):
        pass
