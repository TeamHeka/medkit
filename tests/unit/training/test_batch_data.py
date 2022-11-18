import pytest

from medkit.training.utils import BatchData


def test_get_attributes():
    data = BatchData(inputs=[0, 1, 2])
    assert data.inputs == [0, 1, 2]
    with pytest.raises(AttributeError):
        _ = data.outputs
    assert data[0] == {"inputs": 0}


def test_index_int():
    data = BatchData(inputs=["hello", "world"], outputs=["bonjour", "monde"])
    assert data[0] == {"inputs": "hello", "outputs": "bonjour"}
    assert data[1] == {"inputs": "world", "outputs": "monde"}
    assert data[0:1] == {"inputs": ["hello"], "outputs": ["bonjour"]}
    assert data[:] == {"inputs": ["hello", "world"], "outputs": ["bonjour", "monde"]}


def test_dict_properties():
    data = BatchData(inputs=["hello", "world"], outputs=["bonjour", "monde"])
    assert list(data) == ["inputs", "outputs"]
    assert list(data.values()) == [["hello", "world"], ["bonjour", "monde"]]
