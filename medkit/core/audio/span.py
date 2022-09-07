from __future__ import annotations

__all__ = ["Span"]

from typing import Any, Dict, NamedTuple


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
        return dict(start=self.start, end=self.end)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Span:
        return cls(start=data["start"], end=data["end"])


# TODO: support speed variations? ex: speeded up segment with shorter span
# but referencing span longer span in original audio
