import pytest

from medkit.core import generate_id
from medkit.core.prov_graph import ProvGraph, ProvNode


def test_basic():
    """Basic usage"""
    node_1 = ProvNode(
        data_item_id=generate_id(), operation_id=generate_id(), source_ids=[]
    )
    node_2 = ProvNode(
        data_item_id=generate_id(),
        operation_id=generate_id(),
        source_ids=[node_1.data_item_id],
    )
    node_1.derived_ids.append(node_2.data_item_id)
    graph = ProvGraph([node_1, node_2])

    assert graph.get_nodes() == [node_1, node_2]
    assert graph.has_node(node_1.data_item_id)
    assert graph.get_node(node_1.data_item_id) == node_1
    fake_id = generate_id()
    assert not graph.has_node(fake_id)

    node_3 = ProvNode(data_item_id=generate_id(), operation_id=None, source_ids=[])
    graph.add_node(node_3)
    assert graph.get_nodes() == [node_1, node_2, node_3]
    assert graph.has_node(node_3.data_item_id)
    assert graph.get_node(node_3.data_item_id) == node_3


def test_empty_graph():
    """Empty graph"""
    graph = ProvGraph()
    assert not graph.get_nodes()
    fake_id = generate_id()
    assert not graph.has_node(fake_id)


def test_sanity_check():
    """Sanity check of graphs"""
    node_1 = ProvNode(
        data_item_id=generate_id(), operation_id=generate_id(), source_ids=[]
    )
    node_2 = ProvNode(
        data_item_id=generate_id(), operation_id=generate_id(), source_ids=[]
    )
    node_1.source_ids.append(node_2.data_item_id)
    node_2.derived_ids.append(node_1.data_item_id)
    # valid graph should not raise
    graph_1 = ProvGraph([node_1, node_2])
    graph_1.check_sanity()

    # node with sources but no operation
    node_3 = ProvNode(
        data_item_id=generate_id(), operation_id=None, source_ids=[node_2.data_item_id]
    )
    graph_2 = ProvGraph([node_3])
    with pytest.raises(
        Exception, match="Node with id .* has source ids but no operation"
    ):
        graph_2.check_sanity()

    # node with source id not corresponding to any node
    node_4 = ProvNode(
        data_item_id=generate_id(),
        operation_id=generate_id(),
        source_ids=[generate_id()],
    )
    graph_3 = ProvGraph([node_4])
    with pytest.raises(
        Exception, match="Source id .* in node with id .* has no corresponding node"
    ):
        graph_3.check_sanity()

    # node with derived id not corresponding to any node
    node_4 = ProvNode(
        data_item_id=generate_id(),
        operation_id=None,
        source_ids=[],
        derived_ids=[generate_id()],
    )
    graph_4 = ProvGraph([node_4])
    with pytest.raises(
        Exception, match="Derived id .* in node with id .* has no corresponding node"
    ):
        graph_4.check_sanity()

    source_id = generate_id()
    derived_id = generate_id()
    # derived node with source id but source node does not have derived id
    node_5 = ProvNode(
        data_item_id=source_id,
        operation_id=None,
        source_ids=[],
        derived_ids=[],
    )
    node_6 = ProvNode(
        data_item_id=derived_id,
        operation_id=generate_id(),
        source_ids=[source_id],
        derived_ids=[],
    )
    graph_5 = ProvGraph([node_5, node_6])
    with pytest.raises(
        Exception,
        match=(
            "Node with id .* has source item with id .* but reciprocate derivation link"
            " does not exists"
        ),
    ):
        graph_5.check_sanity()

    # source node with derived id but derived node does not have source id
    node_5 = ProvNode(
        data_item_id=source_id,
        operation_id=None,
        source_ids=[],
        derived_ids=[derived_id],
    )
    node_6 = ProvNode(
        data_item_id=derived_id,
        operation_id=generate_id(),
        source_ids=[],
        derived_ids=[],
    )
    graph_5 = ProvGraph([node_5, node_6])
    with pytest.raises(
        Exception,
        match=(
            "Node with id .* has derived item with id .* but reciprocate source link"
            " does not exists"
        ),
    ):
        graph_5.check_sanity()
