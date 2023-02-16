__all__ = ["Document"]

from typing_extensions import Protocol, runtime_checkable

from medkit.core.annotation import AnnotationType
from medkit.core.annotation_container import AnnotationContainer


@runtime_checkable
class Document(Protocol[AnnotationType]):
    """
    Base document protocol that must be implemented by document classes of all
    modalities (text, audio, etc).

    Documents can contain :class:`~medkit.core.annotation.Annotation` objects.

    Attributes
    ----------
    uid:
        Unique identifier of the document
    anns:
        Annotations of the document, stored in an
        :class:`~medkit.core.annotation_container.AnnotationContainer` for
        easier access (can be subclassed to add modality-specific features).
    """

    uid: str
    anns: AnnotationContainer[AnnotationType]
