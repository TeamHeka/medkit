__all__ = ["IdentifiableDataItem", "IdentifiableDataItemWithAttrs"]

from typing import Generic, Iterable, TypeVar
from typing_extensions import Protocol, runtime_checkable


class IdentifiableDataItem(Protocol):
    uid: str


IdentifiableDataItemType = TypeVar(
    "IdentifiableDataItemType", bound=IdentifiableDataItem
)


@runtime_checkable
class IdentifiableDataItemWithAttrs(Protocol, Generic[IdentifiableDataItemType]):
    attrs: Iterable[IdentifiableDataItemType]
