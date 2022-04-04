__all__ = ["IdentifiableDataItem", "IdentifiableDataItemWithAttrs"]

from typing import Generic, List, Protocol, TypeVar, runtime_checkable


class IdentifiableDataItem(Protocol):
    id: str


IdentifiableDataItemType = TypeVar(
    "IdentifiableDataItemType", bound=IdentifiableDataItem
)


@runtime_checkable
class IdentifiableDataItemWithAttrs(Protocol, Generic[IdentifiableDataItemType]):
    attrs: List[IdentifiableDataItemType]
