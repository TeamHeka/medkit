import abc
from typing import List, Optional, Union

from medkit.core.collection import Collection
from medkit.core.document import Document


class InputConverter:
    """Abstract class for converting external document to medkit documents"""

    @abc.abstractmethod
    def load(self, **kwargs) -> Collection:
        raise NotImplementedError


class OutputConverter:
    """Abstract class for converting medkit document to external format"""

    @abc.abstractmethod
    def save(self, docs: Union[List[Document], Collection], **kwargs) -> Optional[List]:
        raise NotImplementedError
