__all__ = ["save_prov_to_dot"]

from pathlib import Path
from typing import Any, Callable, Dict, TextIO, Optional, Type, Union

from medkit.core import (
    OperationDescription,
    Store,
    ProvGraph,
    ProvNode,
    IdentifiableDataItem,
    IdentifiableDataItemWithAttrs,
    Attribute,
)
from medkit.core.text import Segment


def save_prov_to_dot(
    prov_graph: ProvGraph,
    store: Store,
    file: Union[str, Path],
    data_item_formatters: Optional[Dict[Type, Callable[[Any], str]]] = None,
    op_formatter: Optional[Callable[[OperationDescription], str]] = None,
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
        Path to the .dot file.
    data_item_formatters:
        Dict mapping data items types with callback functions returning the text
        to display for each data item of this type.
        Some default formatters are available for common data item such as text
        annotations. Use `data_item_formatters` to override them or to add support
        for other types.
    op_formatter:
        Callback function returning the text to display for each operation.
        If none provided, the operation name is used.
    max_sub_graph_depth:
        When there are nested provenance sub graphs for some operations, how
        deep should we go when displaying the contents of these sub graphs.
    show_attr_links:
        Wether to show links between attributes and the data items they are
        attached to (not strictly provenance but can make things easier to
        understand).
    """
    with open(file, mode="w") as fp:
        writer = _DotWriter(
            store,
            fp,
            data_item_formatters,
            op_formatter,
            max_sub_graph_depth,
            show_attr_links,
        )
        writer.write_graph(prov_graph)


_DEFAULT_DATA_ITEMS_FORMATTERS = {
    Segment: lambda s: f"{s.label}: {s.text}",
    Attribute: lambda a: f"{a.label}: {a.value}",
}


class _DotWriter:
    def __init__(
        self,
        store: Store,
        fp: TextIO,
        data_item_formatters: Optional[Dict[Type, Callable[[Any], str]]],
        op_formatter: Optional[Callable[[OperationDescription], str]],
        max_sub_graph_depth: Optional[int],
        show_attr_links: bool = True,
    ):
        if data_item_formatters is None:
            data_item_formatters = {}

        self._store = store
        self._fp = fp
        self._data_item_formatters = data_item_formatters
        self._op_formatter = op_formatter
        self._max_sub_graph_depth = max_sub_graph_depth
        self._show_attr_links = show_attr_links

    def write_graph(self, graph: ProvGraph, current_sub_graph_depth: int = 0):
        if current_sub_graph_depth == 0:
            self._fp.write("digraph {\n\n")

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
            self._fp.write("\n\n}")

    def _write_node(self, node: ProvNode):
        data_item = self._store.get_data_item(node.data_item_id)
        data_item_label = self._format_data_item(data_item)
        self._fp.write(f'"{data_item.id}" [label="{data_item_label}"];\n')

        if node.operation_id is not None:
            op_desc = self._store.get_op_desc(node.operation_id)
            op_label = (
                self._op_formatter(op_desc)
                if self._op_formatter is not None
                else op_desc.name
            )
        else:
            op_label = "Unknown"
        for source_id in node.source_ids:
            self._fp.write(f'"{source_id}" -> "{data_item.id}" [label="{op_label}"];\n')
        self._fp.write("\n\n")

        if self._show_attr_links and isinstance(
            data_item, IdentifiableDataItemWithAttrs
        ):
            for attr in data_item.get_attrs():
                self._fp.write(
                    f'"{data_item.id}" -> "{attr.id}" [style=dashed, color=grey,'
                    ' label="attr", fontcolor=grey];\n'
                )

    def _format_data_item(self, data_item: IdentifiableDataItem):
        # must test first user-provided formatters then default
        # (can't merge the two in same dict, this might create unexpected
        # behavior when there a subtypes)
        for formatters in [self._data_item_formatters, _DEFAULT_DATA_ITEMS_FORMATTERS]:
            for type, formatter in formatters.items():
                if isinstance(data_item, type):
                    return formatter(data_item)
        raise ValueError(
            f"Found no formatter for data item with type {type(data_item)}, please"
            " provide one"
        )
