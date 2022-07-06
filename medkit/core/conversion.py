import abc
from typing import List, Optional, Union

from medkit.core.document import Collection, Document
from medkit.core.operation import Operation


class InputConverter(Operation):
    """Abstract class for converting external document to medkit documents"""

    @abc.abstractmethod
    def load(self, **kwargs) -> Collection:
        raise NotImplementedError


class OutputConverter:
    """Abstract class for converting medkit document to external format"""

    @abc.abstractmethod
    def convert(
        self, docs: Union[List[Document], Collection], **kwargs
    ) -> Optional[List]:
        raise NotImplementedError
