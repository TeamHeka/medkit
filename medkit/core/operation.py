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
from typing import Any, Dict, List, Tuple, Union

from medkit.core.id import generate_id
from medkit.core.document import Collection
from medkit.core.annotation import Annotation


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
    config: Dict[str, Any] = dataclasses.field(default_factory=dict)


class ProcessingOperation(Operation):
    """Operation that processes annotations"""

    @abc.abstractmethod
    def process(
        self, **all_input_annotations: List[Annotation]
    ) -> Union[None, List[Annotation], Tuple[List[Annotation], ...]]:
        """Main processing function to implement

        Params
        ------
        all_input_annotations:
            One or several list of annotations to process
            (according to the number of input the operation needs)

        Returns
        -------
        Union[None, List[Annotation], Tuple[List[Annotation], ...]]
            Tuple of list of all new annotations created by the operation.
            Can be None if the operation does not create any new annotation
            but rather modify input annotations in-place (for instance by
            adding attributes).
            If there is only one list of created annotations, it is possible
            to return directly that list without wrapping it in a tuple.
        """


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
