import abc

from medkit.core.document import Collection


class InputConverter:
    @abc.abstractmethod
    def load(self, **kwargs) -> Collection:
        pass


class OutputConverter:
    @abc.abstractmethod
    def save(self, collection: Collection):
        pass
