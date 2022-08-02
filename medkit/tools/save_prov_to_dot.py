__all__ = ["save_prov_to_dot"]

from typing import Callable, TextIO, Optional

from medkit.core import (
    OperationDescription,
    Store,
    ProvGraph,
    ProvNode,
    IdentifiableDataItem,
    IdentifiableDataItemWithAttrs,
)


def save_prov_to_dot(
    prov_graph: ProvGraph,
    store: Store,
    file: TextIO,
    data_item_formatter: Callable[[IdentifiableDataItem], str],
    op_formatter: Callable[[OperationDescription], str],
    max_sub_graph_depth: Optional[int] = None,
    show_attr_links: bool = True,
):
    """Generate a graphviz-compatible .dot file from a ProvGraph for
    visualization.

    Parameters
    ----------
    prov_graph:
        Provenance graph to save.
    store:
        Store holding the data items and operation descriptions referenced by
        `prov_graph`.
    file:
        File handle to the .dot file.
    data_item_formatter:
        Callback function returning the label to use for each data item.
    op_formatter:
        Callback function returning the label to use for each operation.
    max_sub_graph_depth:
        When there are nested provenance sub graphs for some operations, how
        deep should we go when displaying the contents of these sub graphs.
    show_attr_links:
        Wether to show links between attributes and the data items they are
        attached to (not strictly provenance but can make things easier to
        understand).
    """
    writer = _DotWriter(
        store,
        file,
        data_item_formatter,
        op_formatter,
        max_sub_graph_depth,
        show_attr_links,
    )
    writer.write_graph(prov_graph)


class _DotWriter:
    def __init__(
        self,
        store: Store,
        file: TextIO,
        data_item_formatter: Callable[[IdentifiableDataItem], str],
        op_formatter: Callable[[OperationDescription], str],
        max_sub_graph_depth: Optional[int],
        show_attr_links: bool = True,
    ):
        self._store = store
        self._file = file
        self._data_item_formatter = data_item_formatter
        self._op_formatter = op_formatter
        self._max_sub_graph_depth = max_sub_graph_depth
        self._show_attr_links = show_attr_links

    def write_graph(self, graph: ProvGraph, current_sub_graph_depth: int = 0):
        if current_sub_graph_depth == 0:
            self._file.write("digraph {\n\n")

        write_sub_graph = (
            self._max_sub_graph_depth is None
            or current_sub_graph_depth < self._max_sub_graph_depth
        )

        for node in graph.get_nodes():
            if (
                not write_sub_graph
                or node.operation_id is None
                or not graph.has_sub_graph(node.operation_id)
            ):
                self._write_node(node)

        if write_sub_graph:
            for sub_graph in graph.get_sub_graphs():
                self.write_graph(sub_graph, current_sub_graph_depth + 1)

        if current_sub_graph_depth == 0:
            self._file.write("\n\n}")

    def _write_node(self, node: ProvNode):
        data_item = self._store.get_data_item(node.data_item_id)
        data_item_label = self._data_item_formatter(data_item)
        self._file.write(f'"{data_item.id}" [label="{data_item_label}"];\n')

        if node.operation_id is not None:
            op_desc = self._store.get_op_desc(node.operation_id)
            op_label = self._op_formatter(op_desc)
        else:
            op_label = "Unknown"
        for source_id in node.source_ids:
            self._file.write(
                f'"{source_id}" -> "{data_item.id}" [label="{op_label}"];\n'
            )
        self._file.write("\n\n")

        if self._show_attr_links and isinstance(
            data_item, IdentifiableDataItemWithAttrs
        ):
            for attr in data_item.get_attrs():
                self._file.write(
                    f'"{data_item.id}" -> "{attr.id}" [style=dashed, color=grey,'
                    ' label="attr", fontcolor=grey];\n'
                )
