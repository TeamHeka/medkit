__all__ = ["Store", "DictStore"]

from typing import Dict
from typing_extensions import Protocol, runtime_checkable

from medkit.core.data_item import IdentifiableDataItem
from medkit.core.operation_desc import OperationDescription


@runtime_checkable
class Store(Protocol):
    def store_data_item(self, data_item: IdentifiableDataItem):
        pass

    def get_data_item(self, data_item_id: str) -> IdentifiableDataItem:
        pass

    def store_op_desc(self, op_desc: OperationDescription):
        pass

    def get_op_desc(self, operation_id: str) -> OperationDescription:
        pass


class DictStore:
    def __init__(self) -> None:
        self._data_items_by_id: Dict[str, IdentifiableDataItem] = {}
        self._op_descs_by_id: Dict[str, OperationDescription] = {}

    def store_data_item(self, data_item: IdentifiableDataItem):
        self._data_items_by_id[data_item.uid] = data_item

    def get_data_item(self, data_item_id: str) -> IdentifiableDataItem:
        return self._data_items_by_id[data_item_id]

    def store_op_desc(self, op_desc: OperationDescription):
        self._op_descs_by_id[op_desc.uid] = op_desc

    def get_op_desc(self, operation_id: str) -> OperationDescription:
        return self._op_descs_by_id[operation_id]
