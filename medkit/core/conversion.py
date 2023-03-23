__all__ = ["InputConverter", "OutputConverter"]

import abc
from typing import List, Optional

from medkit.core.document import Document


class InputConverter:
    """Abstract class for converting external document to medkit documents"""

    @abc.abstractmethod
    def load(self, **kwargs) -> List[Document]:
        raise NotImplementedError


class OutputConverter:
    """Abstract class for converting medkit document to external format"""

    @abc.abstractmethod
    def save(self, docs: List[Document], **kwargs) -> Optional[List]:
        raise NotImplementedError
