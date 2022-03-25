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

from medkit.core.document import Collection


class Operation(abc.ABC):
    """Any medkit operation (io convertor, processing operation, etc)"""

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
    id: str
    config: Dict[str, Any] = dataclasses.field(default_factory=dict)


class ProcessingOperation(Operation):
    """Operation that processes data items"""

    @abc.abstractmethod
    def process(
        self, **all_input_data: List[Any]
    ) -> Union[None, List[Any], Tuple[List[Any], ...]]:
        """Main processing function to implement

        Params
        ------
        all_input_data:
            One or several list of data items to process
            (according to the number of input the operation needs)

        Returns
        -------
        Union[None, List[Any], Tuple[List[Any], ...]]
            Tuple of list of all new data items created by the operation.
            Can be None if the operation does not create any new data items
            but rather modify existing items in-place (for instance by
            adding attributes to existing annotations).
            If there is only one list of created data items, it is possible
            to return directly that list without wrapping it in a tuple.
        """


class RuleBasedAnnotator(ProcessingOperation):
    pass


class InputConverter(Operation):
    @abc.abstractmethod
    def load(self, **kwargs) -> Collection:
        pass


class OutputConverter(Operation):
    @abc.abstractmethod
    def save(self, collection: Collection):
        pass
