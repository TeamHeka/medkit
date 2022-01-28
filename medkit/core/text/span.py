__all__ = ["Span"]

from typing import NamedTuple


class Span(NamedTuple):
    start: int
    end: int

    def contains(self, other_span):
        return self.start <= other_span.start and self.end >= other_span.end
