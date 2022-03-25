__all__ = ["save_prov_to_dot"]

from typing import Callable, TextIO, Optional
import warnings

from medkit.core import Document, Annotation, OperationDescription, ProvGraph, ProvNode


def save_prov_to_dot(
    prov_graph: ProvGraph,
    doc: Document,
    file: TextIO,
    ann_formatter: Callable[[Annotation], str],
    op_formatter: Callable[[OperationDescription], str],
    max_sub_graph_depth: Optional[int] = None,
):
    """Generate a graphviz-compatible .dot file from a ProvGraph for visualization"""
    writer = _DotWriter(
        doc,
        file,
        ann_formatter,
        op_formatter,
        max_sub_graph_depth,
    )
    writer.write_graph(prov_graph)


class _DotWriter:
    def __init__(
        self,
        doc: Document,
        file: TextIO,
        ann_formatter: Callable[[Annotation], str],
        op_formatter: Callable[[OperationDescription], str],
        max_sub_graph_depth: Optional[int],
    ):
        self._doc: Document = doc
        self._file: TextIO = file
        self._ann_formatter: Callable[[Annotation], str] = ann_formatter
        self._op_formatter: Callable[[OperationDescription], str] = op_formatter
        self._max_sub_graph_depth: Optional[int] = max_sub_graph_depth

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
        ann_id = node.data_item_id
        ann = self._doc.get_annotation_by_id(ann_id)
        if ann is None:
            warnings.warn(
                f"Couldn't find annotation with id {ann_id}, maybe it is an attribute?"
            )
            ann_label = "Unknown"
        else:
            ann_label = self._ann_formatter(ann)
        self._file.write(f'"{ann_id}" [label="{ann_label}"];\n')

        if node.operation_id is not None:
            op_desc = self._doc.get_operation_by_id(node.operation_id)
            op_label = self._op_formatter(op_desc)
        else:
            op_label = "Unknown"
        for source_id in node.source_ids:
            self._file.write(f'"{source_id}" -> "{ann_id}" [label="{op_label}"];\n')
        self._file.write("\n\n")
