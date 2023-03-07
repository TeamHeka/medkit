from __future__ import annotations

__all__ = ["Span"]

from typing import Any, Dict, NamedTuple

from medkit.core import dict_conv


class Span(NamedTuple):
    """
    Boundaries of a slice of audio.

    Parameters
    ----------
    start:
        Starting point in the original audio, in seconds.
    end:
        Ending point in the original audio, in seconds.
    """

    start: float
    end: float

    @property
    def length(self):
        """Length of the span, in seconds"""
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        span_dict = dict(start=self.start, end=self.end)
        dict_conv.add_class_name_to_data_dict(self, span_dict)
        return span_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Span:
        dict_conv.check_class_matches_data_dict(cls, data)
        return cls(start=data["start"], end=data["end"])


# TODO: support speed variations? ex: speeded up segment with shorter span
# but referencing span longer span in original audio
