__all__ = [
    "DictSerializable",
    "dict_serializable",
    "is_deserializable",
    "serialize",
    "deserialize",
]


from typing import Any, Dict, Type, TypeVar
from typing_extensions import Self, Protocol, runtime_checkable


DictSerializableType = TypeVar("DictSerializableType", bound="DictSerializable")


@runtime_checkable
class DictSerializable(Protocol):
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        pass


_class_name_to_class: Dict[str, Type[DictSerializable]] = {}
_CLASS_NAME_KEY = "_class_name"


def dict_serializable(
    class_: Type[DictSerializableType],
) -> Type[DictSerializableType]:
    if not issubclass(class_, DictSerializable):
        raise ValueError(
            f"Class '{class_}' does not provide required from_dict() and"
            " to_dict() methods"
        )

    class_name = _get_class_name(class_)
    _class_name_to_class[class_name] = class_
    return class_


def is_deserializable(object: Dict):
    return isinstance(object, dict) and object.get(_CLASS_NAME_KEY) is not None


def serialize(object: DictSerializable) -> Dict[str, Any]:
    class_name = _get_class_name(object.__class__)
    if class_name not in _class_name_to_class:
        raise ValueError(
            f"No class found for class name '{class_name}', make sure you"
            " decorate the class with @dict_serializable"
        )

    data = object.to_dict()
    data[_CLASS_NAME_KEY] = class_name
    return data


def deserialize(data: Dict[str, Any]) -> DictSerializable:
    data = data.copy()
    class_name = data.pop(_CLASS_NAME_KEY, None)
    if class_name is None:
        raise ValueError(
            f"data_dict is not deserializable (should contain a '{_CLASS_NAME_KEY}'"
            " key). Make sure it was created with the serialize() function."
        )

    class_ = _class_name_to_class.get(class_name)
    if class_ is None:
        raise ValueError(
            f"No class found for class name '{class_name}', make sure you"
            " decorate the class with @dict_serializable and import it"
        )

    return class_.from_dict(data)


def _get_class_name(class_: Type[DictSerializable]) -> str:
    return class_.__module__ + "." + class_.__qualname__
