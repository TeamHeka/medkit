import abc

from medkit.core.document import Collection


class InputConverter:
    """Abstract class for converting external document to medkit documents"""

    @abc.abstractmethod
    def load(self, **kwargs) -> Collection:
        pass


class OutputConverter:
    """Abstract class for converting medkit document to external format"""

    @abc.abstractmethod
    def save(self, collection: Collection):
        pass
