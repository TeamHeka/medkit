__all__ = ["Store", "GlobalStore"]

from typing import Dict, Union
from typing_extensions import Protocol, runtime_checkable

from medkit.core.data_item import IdentifiableDataItem


@runtime_checkable
class Store(Protocol):
    def store_data_item(self, data_item: IdentifiableDataItem, parent_id: str):
        pass

    def get_data_item(self, data_item_id: str) -> IdentifiableDataItem:
        pass

    def get_parent_item(self, data_item) -> IdentifiableDataItem:
        pass


class _DictStore:
    def __init__(self) -> None:
        self._data_items_by_id: Dict[str, IdentifiableDataItem] = {}
        self._parent_ids_by_id: Dict[str, str] = {}

    def store_data_item(self, data_item: IdentifiableDataItem, parent_id: str):
        self._data_items_by_id[data_item.uid] = data_item
        self._parent_ids_by_id[data_item.uid] = parent_id

    def get_data_item(self, data_item_id: str) -> IdentifiableDataItem:
        return self._data_items_by_id[data_item_id]

    def get_parent_item(self, data_item_id: str) -> IdentifiableDataItem:
        parent_id = self._parent_ids_by_id[data_item_id]
        return self._data_items_by_id.get(parent_id, None)


class GlobalStore:
    _store: Union[Store, None] = None

    @classmethod
    def init_store(cls, store: Store) -> Store:
        if cls._store is None:
            cls._store = store
        else:
            raise RuntimeError(
                "The global store has already been initialized. If it was not your"
                " intention, please put this line at the beginning of your script to"
                " make sure to set global store before any other initialization"
            )
        return cls._store

    @classmethod
    def get_store(cls) -> Store:
        if cls._store is None:
            cls._store = _DictStore()
        return cls._store

    @classmethod
    def del_store(cls):
        cls._store = None
