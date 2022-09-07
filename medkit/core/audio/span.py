__all__ = ["Span"]

from typing import NamedTuple


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


# TODO: support speed variations? ex: speeded up segment with shorter span
# but referencing span longer span in original audio
