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


def _gen_simple_graph():
    graph = ProvGraph()

    node_1 = ProvNode(
        data_item_id=generate_id(), operation_id=generate_id(), source_ids=[]
    )
    graph.add_node(node_1)

    node_2 = ProvNode(
        data_item_id=generate_id(),
        operation_id=generate_id(),
        source_ids=[node_1.data_item_id],
    )
    graph.add_node(node_2)

    node_3 = ProvNode(
        data_item_id=generate_id(),
        operation_id=generate_id(),
        source_ids=[node_2.data_item_id],
    )
    graph.add_node(node_3)

    return graph


def test_sub_graph_basic():
    """Basic behavior of graph with 2 sub graphs"""
    graph = _gen_simple_graph()

    # add a sub graph corresponding to an operation in the main
    node_1 = graph.get_nodes()[0]
    sub_graph_1 = _gen_simple_graph()
    graph.add_sub_graph(node_1.operation_id, sub_graph_1)
    assert graph.get_sub_graphs() == [sub_graph_1]
    assert graph.has_sub_graph(node_1.operation_id)
    assert graph.get_sub_graph(node_1.operation_id) == sub_graph_1

    # add another sub graph for a different operation
    node_2 = graph.get_nodes()[1]
    sub_graph_2 = _gen_simple_graph()
    graph.add_sub_graph(node_2.operation_id, sub_graph_2)
    assert graph.get_sub_graphs() == [sub_graph_1, sub_graph_2]
    assert graph.has_sub_graph(node_2.operation_id)
    assert graph.get_sub_graph(node_2.operation_id) == sub_graph_2

    # add a sub graph for an operation not in the main graph
    sub_graph_3 = _gen_simple_graph()
    graph.add_sub_graph(generate_id(), sub_graph_3)


def test_multiple_subgraphs_for_same_op():
    """Adding 2 sub graphs for the same operation (they should be merged)"""
    graph = _gen_simple_graph()

    # add a sub graph corresponding to an operation in the main graph
    node_1 = graph.get_nodes()[0]
    op_id = node_1.operation_id
    sub_graph_1 = _gen_simple_graph()
    graph.add_sub_graph(op_id, sub_graph_1)
    assert graph.get_sub_graph(op_id).get_nodes() == sub_graph_1.get_nodes()

    # add another subgraph for the same operation
    sub_graph_2 = _gen_simple_graph()
    graph.add_sub_graph(op_id, sub_graph_2)
    # both sub graphs should be merged into a new sub graph with all nodes
    merged_sub_graph = graph.get_sub_graph(op_id)
    assert (
        merged_sub_graph.get_nodes()
        == sub_graph_1.get_nodes() + sub_graph_2.get_nodes()
    )


def test_flatten():
    """Flatten a graph containing subgraphs, without repeating nodes
    with same operation id as subgraph
    """
    graph = _gen_simple_graph()
    # flattening a graph with no subgraphs should return identical graph
    assert graph.flatten().get_nodes() == graph.get_nodes()

    # add a sub graph corresponding to an operation in the main graph
    node_1 = graph.get_nodes()[0]
    sub_graph_1 = _gen_simple_graph()
    graph.add_sub_graph(node_1.operation_id, sub_graph_1)

    flattened_graph_1 = graph.flatten()
    # flattened graph has no subgraphs
    assert not flattened_graph_1.get_sub_graphs()
    # flattened graph should have all nodes in main graph and sub graph,
    # excepted the node with the same operation id as the sub graph
    # (the node was "expanded" in the sub graph)
    expected_nodes_1 = [
        n for n in graph.get_nodes() if n is not node_1
    ] + sub_graph_1.get_nodes()
    assert flattened_graph_1.get_nodes() == expected_nodes_1

    # add another sub graph for another operation in the main graph
    node_2 = graph.get_nodes()[1]
    sub_graph_2 = _gen_simple_graph()
    graph.add_sub_graph(node_2.operation_id, sub_graph_2)
    # flattened graph should have all nodes in main graph and all sub graphs,
    # excepted  nodes with same operation ids as a sub graph
    flattened_graph_2 = graph.flatten()
    expected_nodes_2 = (
        [n for n in graph.get_nodes() if n not in (node_1, node_2)]
        + sub_graph_1.get_nodes()
        + sub_graph_2.get_nodes()
    )
    assert flattened_graph_2.get_nodes() == expected_nodes_2


def test_flatten_recursive():
    """Flatten a graph containing subgraphs recursively"""
    graph = _gen_simple_graph()

    # add a sub graph corresponding to an operation in the main graph
    node = graph.get_nodes()[0]
    sub_graph = _gen_simple_graph()
    graph.add_sub_graph(node.operation_id, sub_graph)

    # add a sub graph in the sub graph (test recursion)
    sub_node = sub_graph.get_nodes()[0]
    sub_sub_graph = _gen_simple_graph()
    sub_graph.add_sub_graph(sub_node.operation_id, sub_sub_graph)
    flattened_graph = graph.flatten()
    expected_nodes = (
        [n for n in graph.get_nodes() if n is not node]
        + [n for n in sub_graph.get_nodes() if n is not sub_node]
        + sub_sub_graph.get_nodes()
    )
    assert flattened_graph.get_nodes() == expected_nodes


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

    # valid graph with invalid sub_graph
    sub_graphs_by_op_id = {generate_id(): graph_3}
    graph_6 = ProvGraph([node_1, node_2], sub_graphs_by_op_id)
    with pytest.raises(Exception, match="Source id .* has no corresponding node"):
        graph_6.check_sanity()
