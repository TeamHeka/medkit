from __future__ import annotations

__all__ = ["Annotation", "Attribute", "Origin"]

import abc
import dataclasses
from typing import Dict, List, Optional

from medkit.core.id import generate_id


class Annotation(abc.ABC):
    def __init__(
        self,
        origin: Origin,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        ann_id: str = None,
        metadata: Dict = None,
    ):
        """
        Provide common initialization for annotation instances

        Parameters
        ----------
        origin: Origin
            Description of how this annotation was generated
        label: str
            The annotation label
        attrs:
            The attributes of the annotation
        ann_id: str, Optional
            The annotation id
        metadata: dict
            The dictionary containing the annotation metadata
        """
        if ann_id:
            self.id = ann_id
        else:
            self.id = generate_id()
        if attrs is None:
            attrs = []

        self.origin = origin
        self.label = label
        self.attrs: List[Attribute] = attrs
        self.metadata = metadata

    def add_metadata(self, key, value):
        if self.metadata is None:
            self.metadata = {}
        if key in self.metadata.keys():
            raise ValueError(f"Metadata key {key} is already used")
        self.metadata[key] = value

    @abc.abstractmethod
    def __repr__(self):
        return (
            f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r},"
            f" nb_attrs={len(self.attrs)}"
        )


class Attribute:
    def __init__(self, origin, label, value=None, attr_id=None, metadata=None):
        """
        Initialize a medkit attribute, to be added to an annotation

        Parameters
        ----------
        origin: Origin
            Description of how this attribute annotation was generated
        label: str
            The attribute label
        value: str, Optional
            The value of the attribute
        attr_id: str, Optional
            The id of the attribute (if existing)
        metadata: Dict[str, Any], Optional
            The metadata of the attribute
        """
        if attr_id:
            attr_id = generate_id()

        self.id = attr_id
        self.origin = origin
        self.label = label
        self.metadata = metadata
        self.value = value

    def add_metadata(self, key, value):
        if self.metadata is None:
            self.metadata = {}
        if key in self.metadata.keys():
            raise ValueError(f"Metadata key {key} is already used")
        self.metadata[key] = value

    @abc.abstractmethod
    def __repr__(self):
        return (
            f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r},"
            f" value={self.value}"
        )


@dataclasses.dataclass(frozen=True)
class Origin:
    """Description of how an annotation was generated

    Parameters
    ----------
    operation_id:
        Identifier of the `OperationDescription` describing
        the processing module that generated the annotation.
        Should never be None except for RAW_TEXT annotation.

    ann_ids:
        Identifier of the source annotations that were used
        to generate the annotation. Typically there will
        only be one source annotation but there might be none
        or several.
    """

    operation_id: Optional[str] = None
    ann_ids: List[str] = dataclasses.field(default_factory=list)
