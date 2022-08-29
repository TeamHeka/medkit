from __future__ import annotations

__all__ = ["ProvBuilder"]

import collections
from typing import List, Optional

from medkit.core.data_item import IdentifiableDataItem
from medkit.core.operation_desc import OperationDescription
from medkit.core.prov_graph import ProvGraph
from medkit.core.store import Store, DictStore


class ProvBuilder:
    def __init__(self, store: Optional[Store] = None):
        if store is None:
            store = DictStore()

        self.store: Store = store
        self.graph: ProvGraph = ProvGraph()

    def add_prov(
        self,
        data_item: IdentifiableDataItem,
        op_desc: OperationDescription,
        source_data_items: List[IdentifiableDataItem],
    ):
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

    def add_prov_from_sub_graph(
        self,
        data_items: List[IdentifiableDataItem],
        op_desc: OperationDescription,
        sub_builder: ProvBuilder,
    ):
        assert self.store is sub_builder.store
        self.store.store_op_desc(op_desc)

        sub_graph = sub_builder.graph
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
            self._add_prov_from_sub_graph_for_data_item(
                data_item.id, op_desc.id, sub_graph
            )

    def _add_prov_from_sub_graph_for_data_item(
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

        # add new node on main graph for group operation
        self.graph.add_node(data_item_id, operation_id, source_ids)
