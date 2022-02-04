__all__ = ["Span"]

from typing import NamedTuple


class Span(NamedTuple):
    start: int
    end: int

    @property
    def length(self):
        return self.end - self.start
