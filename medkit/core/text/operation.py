import abc
from typing import List

from medkit.core.operation import Operation
from medkit.core.text.annotation import Entity, Segment


class ContextOperation(Operation):
    """
    Abstract operation for context detection.
    It uses a list of segments as input for running the operation and creates attributes
    that are directly appended to these segments.
    """

    @abc.abstractmethod
    def run(self, segments: List[Segment]) -> None:
        raise NotImplementedError


class NEROperation(Operation):
    """
    Abstract operation for detecting entities.
    It uses a list of segments as input and produces a list of detected entities.
    """

    @abc.abstractmethod
    def run(self, segments: List[Segment]) -> List[Entity]:
        raise NotImplementedError


class SegmentationOperation(Operation):
    """
    Abstract operation for segmenting text.
    It uses a list of segments as input and produces a list of new segments.
    """

    @abc.abstractmethod
    def run(self, segments: List[Segment]) -> List[Segment]:
        raise NotImplementedError
