__all__ = ["IdentifiableDataItem", "IdentifiableDataItemWithAttrs"]

from typing import Generic, List, TypeVar
from typing_extensions import Protocol, runtime_checkable


class IdentifiableDataItem(Protocol):
    id: str


IdentifiableDataItemType = TypeVar(
    "IdentifiableDataItemType", bound=IdentifiableDataItem
)


@runtime_checkable
class IdentifiableDataItemWithAttrs(Protocol, Generic[IdentifiableDataItemType]):
    def get_attrs(self) -> List[IdentifiableDataItemType]:
        ...
