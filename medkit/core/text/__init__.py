__all__ = [
    "TextDocument",
    "Span",
    "TextBoundAnnotation",
    "Entity",
    "Attribute",
    "Relation",
]

from .annotation import Attribute
from .annotation import Entity
from .annotation import Relation
from .annotation import TextBoundAnnotation
from .document import TextDocument
from .span import Span
