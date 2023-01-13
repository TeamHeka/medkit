__all__ = ["DictSerializable"]


from typing import Any, Dict, Type, TypeVar
from typing_extensions import Protocol, runtime_checkable


DictSerializableType = TypeVar("DictSerializableType", bound="DictSerializable")


@runtime_checkable
class DictSerializable(Protocol):
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    def from_dict(
        cls: Type[DictSerializableType], data: Dict[str, Any]
    ) -> DictSerializableType:
        pass
