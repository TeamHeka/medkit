import dataclasses
import pytest

from medkit.core.operation_desc import OperationDescription
from medkit.core.store import _DictStore, GlobalStore


class MockStore:
    @dataclasses.dataclass
    class MockData:
        uid: str

    def store_data_item(self, data_item):
        pass

    def get_data_item(self, data_item_id):
        return self.MockData(uid=data_item_id)

    def store_op_desc(self, op_desc):
        pass

    def get_op_desc(self, op_id):
        return OperationDescription(uid=op_id, name="op")


def test_global_store_init_store():
    store = GlobalStore.init_store(MockStore())
    assert isinstance(store, MockStore)
    store = GlobalStore.get_store()
    assert isinstance(store, MockStore)


def test_global_store_init_store_error():
    store = GlobalStore.get_store()
    assert isinstance(store, _DictStore)
    with pytest.raises(RuntimeError):
        GlobalStore.init_store(MockStore())
