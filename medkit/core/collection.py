__all__ = ["Collection"]

from typing import Any, Dict, List, TypeVar

from medkit.core.annotation import Annotation
from medkit.core.document import Document

AnnotationType = TypeVar("AnnotationType", bound=Annotation)


class Collection:
    """Collection of documents"""

    def __init__(self, documents: List[Document]):
        self.documents = documents

    def to_dict(self) -> Dict[str, Any]:
        documents = [d.to_dict() for d in self.documents]
        return dict(documents=documents)
