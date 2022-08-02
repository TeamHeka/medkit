from __future__ import annotations

__all__ = ["ProvTracer", "Prov"]

import dataclasses
import collections
from typing import List, Optional

from medkit.core.data_item import IdentifiableDataItem
from medkit.core.operation_desc import OperationDescription
from medkit.core.prov_graph import ProvGraph, ProvNode
from medkit.core.store import Store, DictStore


@dataclasses.dataclass
class Prov:
    """Provenance information for a specific data item.

    Parameters
    ----------
    data_item:
        Data item that was created (for instance an annotation or an
        attribute).
    op_desc:
        Description of the operation that created the data item.
    source_data_items:
        Data items that were used by the operation to create the data item.
    derived_data_items:
        Data items that were created by other operations using this data item.
    """

    data_item: IdentifiableDataItem
    op_desc: Optional[OperationDescription]
    source_data_items: List[IdentifiableDataItem]
    derived_data_items: List[IdentifiableDataItem]


class ProvTracer:
    """Provenance tracing component.

    `ProvTracer` is intended to gather provenance information about how all data
    generated by medkit. For each data item (for instance an annotation or an
    attribute), `ProvTracer` can tell the operation that created it, the data
    items that were used to create it, and reciprocally, the data items that were
    derived from it (cf. :class:`~Prov`).

    Provenance-compatible operations should inform the provenance tracer of each
    data item that through the :meth:`~.add_prov` method.

    Users wanting to gather provenance information should instantiate one unique
    `ProvTracer` object and provide it to all operations involved in their data
    processing flow. Once all operations have been executed, they may then
    retrieve provenance info for specific data items through
    :meth:`~.get_prov`, or for all items with :meth:`~.get_provs`.

    Composite operations relying on inner operations (such as pipelines)
    shouldn't call :meth:`~.add_prov` method. Instead, they should instantiate
    their own internal `ProvTracer` and provide it to the operations they rely
    on, then use :meth:`~.add_prov_from_sub_tracer` to integrate
    information from this internal sub-provenance tracer into the main
    provenance tracer that was provided to them.

    This will build sub-provenance information, than can then be retrieved
    through :meth:`~.get_sub_prov_tracer` or :meth:`~.get_sub_prov_tracers`. The
    inner operations of a composite operation can themselves be composite
    operations, leading to a tree-like structure of nested provenance tracers.
    """

    def __init__(
        self, store: Optional[Store] = None, graph: Optional[ProvGraph] = None
    ):
        """
        Parameters
        ----------
        store:
            Store into which to store all traced data items of which we are tracing the
            provenance.
        graph:
            Provenance graph to use, should only be provided when instantiating
            a sub-provenance tracer from a sub-graph.
        """
        if store is None:
            store = DictStore()
        if graph is None:
            graph = ProvGraph()

        self.store: Store = store
        self.graph: ProvGraph = graph

    def add_prov(
        self,
        data_item: IdentifiableDataItem,
        op_desc: OperationDescription,
        source_data_items: List[IdentifiableDataItem],
    ):
        """
        Append provenance information about a specific data item.

        Parameters
        ----------
        data_item:
            Data item that was created.
        op_desc:
            Description of the operation that created the data item.
        source_data_items:
            Data items that were used by the operation to create the data item.
        """
        assert not self.graph.has_node(
            data_item.id
        ), f"Provenance of data item with id {data_item.id} was already added"

        self.store.store_data_item(data_item)
        self.store.store_op_desc(op_desc)
        # add source data items to store
        for source_data_item in source_data_items:
            self.store.store_data_item(source_data_item)

        # add node to graph
        source_ids = [s.id for s in source_data_items]
        self.graph.add_node(data_item.id, op_desc.id, source_ids)

    def add_prov_from_sub_tracer(
        self,
        data_items: List[IdentifiableDataItem],
        op_desc: OperationDescription,
        sub_tracer: ProvTracer,
    ):
        """Append provenance information about data items created by a composite
        operation relying on inner operations (such as a pipeline) having its
        own internal sub-provenance tracer.

        Parameters
        ----------
        data_items:
            Data items created by the composite operation. Should not include
            internal intermediate data items, only the output of the operation.
        op_desc:
            Description of the composite operation that created the data items.
        sub_tracer:
            Internal sub-provenance tracer of the composite operation.
        """
        assert self.store is sub_tracer.store
        self.store.store_op_desc(op_desc)

        sub_graph = sub_tracer.graph
        self.graph.add_sub_graph(op_desc.id, sub_graph)

        for data_item in data_items:
            # ignore data items already known
            # (can happen with attributes being copied from one annotation to another)
            if self.graph.has_node(data_item.id):
                # check operation_id is consistent
                node = self.graph.get_node(data_item.id)
                if node.operation_id != op_desc.id:
                    raise RuntimeError(
                        "Trying to add provenance for sub graph for data item with id"
                        " {data_item.id} that already has a node, but with different"
                        " operation_id"
                    )
                continue
            self._add_prov_from_sub_tracer_for_data_item(
                data_item.id, op_desc.id, sub_graph
            )

    def _add_prov_from_sub_tracer_for_data_item(
        self,
        data_item_id: str,
        operation_id: str,
        sub_graph: ProvGraph,
    ):
        assert not self.graph.has_node(data_item_id)
        assert sub_graph.has_node(data_item_id)

        # find source ids
        source_ids = []
        seen = set()
        queue = collections.deque([data_item_id])
        while queue:
            sub_graph_node_id = queue.popleft()
            seen.add(sub_graph_node_id)

            sub_graph_node = sub_graph.get_node(sub_graph_node_id)
            if sub_graph_node.operation_id is None:
                source_ids.append(sub_graph_node_id)
            queue.extend(id for id in sub_graph_node.source_ids if id not in seen)

        # add new node on main graph representing
        # the data item generation by the composed operation
        self.graph.add_node(data_item_id, operation_id, source_ids)

    def has_prov(self, data_item_id: str) -> bool:
        """Check if the provenance tracer has provenance information about a
        specific data item.

        NB:  this will return `False` if we have provenance info about a data
        item but only in a sub-provenance tracer.

        Parameters
        ----------
        data_item_id:
            Id of the data item.

        Returns
        -------
        bool
            `True` if there is provenance info that can be retrieved with
            :meth:`~get_prov()`.
        """
        return self.graph.has_node(data_item_id)

    def get_prov(self, data_item_id: str) -> Prov:
        """Return provenance information about a specific data item.

        Parameters
        ----------
        data_item_id:
            Id of the data item.

        Returns
        -------
        Prov
            Provenance info about the data item.
        """
        node = self.graph.get_node(data_item_id)
        return self._build_prov_from_node(node)

    def get_provs(self) -> List[Prov]:
        """Return all provenance information about all data items known to the tracer.

        NB:  nested provenance info from sub-provenance tracers will not be returned.

        Returns
        -------
        List[Prov]
            Provenance info about all known data items.
        """
        return [self._build_prov_from_node(node) for node in self.graph.get_nodes()]

    def has_sub_prov_tracer(self, operation_id: str) -> bool:
        """Check if the provenance tracer has a sub-provenance tracer for a
        specific composite operation (such as a pipeline).

        NB:  this will return `False` if there is a sub-provenance tracer for
        the operation but that is not a direct child (i.e. that is deeper in the
        hierarchy).

        Parameters
        -----------
        operation_id:
            Id of the composite operation.

        Returns
        -------
        bool
            `True` if there is a sub-provenance tracer for the operation.
        """
        return self.graph.has_sub_graph(operation_id)

    def get_sub_prov_tracer(self, operation_id: str) -> ProvTracer:
        """Return a sub-provenance tracer containing sub-provenance information from a
        specific composite operation.

        Parameters
        ----------
        operation_id:
            Id of the composite operation.

        Returns
        -------
        ProvTracer
            The sub-provenance tracer containing sub-provenance information from the
            operation.
        """
        sub_graph = self.graph.get_sub_graph(operation_id)
        return ProvTracer(store=self.store, graph=sub_graph)

    def get_sub_prov_tracers(self) -> List[ProvTracer]:
        """
        Return all sub-provenance tracers of the provenance tracer.

        NB:  this will not return sub-provenance tracers that are not direct
        children of this tracer (i.e. that are deeper in the hierarchy).

        Returns
        -------
        List[ProvTracer]
            All sub-provenance tracers of this provenance tracer.
        """
        return [
            ProvTracer(store=self.store, graph=sub_graph)
            for sub_graph in self.graph.get_sub_graphs()
        ]

    def _build_prov_from_node(self, node: ProvNode):
        data_item = self.store.get_data_item(node.data_item_id)
        op_desc = (
            self.store.get_op_desc(node.operation_id)
            if node.operation_id is not None
            else None
        )
        source_data_items = [self.store.get_data_item(id) for id in node.source_ids]
        derived_data_items = [self.store.get_data_item(id) for id in node.derived_ids]
        return Prov(data_item, op_desc, source_data_items, derived_data_items)
