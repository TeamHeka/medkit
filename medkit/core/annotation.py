from __future__ import annotations

__all__ = ["Annotation", "Origin"]

import abc
import dataclasses
from typing import Dict, List, Optional

from medkit.core.id import generate_id


class Annotation(abc.ABC):
    def __init__(
        self, origin: Origin, label: str, ann_id: str = None, metadata: Dict = None
    ):
        """
        Provide common initialization for annotation instances

        Parameters
        ----------
        origin: Origin
            Description of how this annotation was generated
        label: str
            The annotation label
        ann_id: str, Optional
            The annotation id
        metadata: dict
            The dictionary containing the annotation metadata
        """
        if ann_id:
            self.id = ann_id
        else:
            self.id = generate_id()
        self.origin = origin
        self.label = label
        self.metadata = metadata

    def add_metadata(self, key, value):
        if self.metadata is None:
            self.metadata = {}
        if key in self.metadata.keys():
            raise ValueError(f"Metadata key {key} is already used")
        self.metadata[key] = value

    @abc.abstractmethod
    def __repr__(self):
        return f"{self.__class__.__qualname__} : id={self.id!r}, label={self.label!r}"


@dataclasses.dataclass(frozen=True)
class Origin:
    """Description of how an annotation was generated

    Parameters
    ----------
    processing_id:
        Identifier of the `ProcessingDescription` describing
        the processing module that generated the annotation.
        Should never be None except for RAW_TEXT annotation.

    ann_ids:
        Identifier of the source annotations that were used
        to generate the annotation. Typically there will
        only be one source annotation but there might be none
        or several.
    """

    processing_id: Optional[str] = None
    ann_ids: List[str] = dataclasses.field(default_factory=lambda: [])
