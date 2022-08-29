from __future__ import annotations

__all__ = ["Operation", "DocOperation"]

import abc

from typing import List, Type, TypeVar, Union

from medkit.core.document import Collection, Document
from medkit.core.id import generate_id
from medkit.core.operation_desc import OperationDescription
from medkit.core.prov_tracer import ProvTracer

C = TypeVar("C", bound="Operation")


class Operation(abc.ABC):
    """Abstract class for all annotator modules"""

    id: str
    _description: OperationDescription = None
    _prov_tracer: ProvTracer = None

    @abc.abstractmethod
    def __init__(self, op_id=None, **kwargs):
        """
        Common initialization for all annotators:
          * assigning id to operation
          * storing config in description

        Parameters
        ----------
        op_id:
            Operation id
        kwargs:
            All other arguments of the child init

        Examples
        --------
        In the `__init__` function of your annotator, use:

        >>> init_args = locals()
        >>> init_args.pop('self')
        >>> super().__init__(**init_args)
        """
        if op_id is None:
            op_id = generate_id()
        self.id = op_id
        self._description = OperationDescription(
            id=self.id, name=self.__class__.__name__, config=kwargs
        )

    def set_prov_tracer(self, prov_tracer: ProvTracer):
        """
        Enable provenance tracing.

        Parameters
        ----------
        prov_tracer:
            The provenance tracer used to trace the provenance.
        """
        self._prov_tracer = prov_tracer

    @property
    def description(self) -> OperationDescription:
        """Contains all the operation init parameters."""
        return self._description

    @classmethod
    def from_description(cls: Type[C], description: OperationDescription) -> C:
        """
        Allows to re-instantiate an existing operation from a description.

        Parameters
        ----------
        description:
            Operation description saved from a previous medkit usage.

        Returns
        -------
        Operation:
            The corresponding operation class instance generated from the description.

        Raises
        ------
        ValueError:
            when description is not correct or not adapted to the operation.
        """
        if cls.__class__.__name__ == description.name:
            return cls(op_id=description.id, **description.config)
        else:
            raise ValueError(
                "Provided description does not match"
                f" {cls.__class__.__name__} constructor"
            )

    def check_sanity(self) -> bool:
        # TODO: add some checks
        pass


class DocOperation(Operation):
    """
    Abstract operation directly executed on text documents.
    It uses a list of documents as input for running the operation and creates
    annotations that are directly appended to these documents.
    """

    @abc.abstractmethod
    def run(self, docs: Union[List[Document], Collection]) -> None:
        raise NotImplementedError
