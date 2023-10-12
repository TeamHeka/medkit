from __future__ import annotations

__all__ = [
    "AnySpan",
    "Span",
    "ModifiedSpan",
]

import abc
import dataclasses
from typing import Any, Dict, List
from typing_extensions import Self

from medkit.core import dict_conv


class AnySpan(abc.ABC, dict_conv.SubclassMapping):
    length: int

    def __init_subclass__(cls):
        AnySpan.register_subclass(cls)
        super().__init_subclass__()

    @classmethod
    def from_dict(cls, ann_dict: Dict[str, Any]) -> Self:
        subclass = cls.get_subclass_for_data_dict(ann_dict)
        if subclass is None:
            raise NotImplementedError(
                "AnySpan is an abstract class. Its class method `from_dict` is"
                " only used for calling the correct subclass `from_dict`"
            )
        return subclass.from_dict(ann_dict)

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class Span(AnySpan):
    """
    Slice of text extracted from the original text

    Parameters
    ----------
    start: int
        Index of the first character in the original text
    end: int
        Index of the last character in the original text, plus one
    """

    start: int
    end: int

    @property
    def length(self):
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        span_dict = dict(start=self.start, end=self.end)
        dict_conv.add_class_name_to_data_dict(self, span_dict)
        return span_dict

    def overlaps(self, other: Span):
        """Test if 2 spans reference at least one character in common"""
        return (self.start < other.end) and (self.end > other.start)

    @classmethod
    def from_dict(cls, span_dict: Dict[str, Any]) -> Self:
        """
        Creates a Span from a dict

        Parameters
        ----------
        span_dict: dict
            A dictionary from a serialized span as generated by to_dict()
        """
        return cls(start=span_dict["start"], end=span_dict["end"])


@dataclasses.dataclass
class ModifiedSpan(AnySpan):
    """
    Slice of text not present in the original text

    Parameters
    ----------
    length:
        Number of characters
    replaced_spans:
        Slices of the original text that this span is replacing
    """

    length: int
    replaced_spans: List[Span]

    def to_dict(self) -> Dict[str, Any]:
        replaced_spans = [s.to_dict() for s in self.replaced_spans]
        span_dict = dict(
            length=self.length,
            replaced_spans=replaced_spans,
        )
        dict_conv.add_class_name_to_data_dict(self, span_dict)
        return span_dict

    @classmethod
    def from_dict(cls, modified_span_dict: Dict[str, Any]) -> Self:
        """
        Creates a Modified from a dict

        Parameters
        ----------
        modified_span_dict: dict
            A dictionary from a serialized ModifiedSpan as generated by to_dict()
        """

        replaced_spans = [
            Span.from_dict(s) for s in modified_span_dict["replaced_spans"]
        ]
        return cls(modified_span_dict["length"], replaced_spans)
