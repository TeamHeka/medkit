from __future__ import annotations

__all__ = ["ProvBuilder"]

import collections
from typing import List, Optional

from medkit.core.data_item import IdentifiableDataItem
from medkit.core.operation_desc import OperationDescription
from medkit.core.prov_graph import ProvGraph, ProvNode
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

        source_ids = [s.id for s in source_data_items]
        node = ProvNode(data_item.id, op_desc.id, source_ids)
        self.graph.add_node(node)

        # add derivation edges
        for source_data_item in source_data_items:
            source_id = source_data_item.id
            # create stub node for unknown source id
            if not self.graph.has_node(source_id):
                source_node = ProvNode(
                    source_id,
                    operation_id=None,
                    source_ids=[],
                    derived_ids=[data_item.id],
                )
                self.graph.add_node(source_node)
            else:
                source_node = self.graph.get_node(source_id)
                source_node.derived_ids.append(data_item.id)
            # add source data item to store
            self.store.store_data_item(source_data_item)

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
        group_node = ProvNode(data_item_id, operation_id, source_ids)
        self.graph.add_node(group_node)

        # add derivation edges
        for source_id in source_ids:
            # create stub node for unknown source id
            if not self.graph.has_node(source_id):
                source_node = ProvNode(
                    source_id,
                    operation_id=None,
                    source_ids=[],
                    derived_ids=[data_item_id],
                )
                self.graph.add_node(source_node)
            else:
                source_node = self.graph.get_node(source_id)
                source_node.derived_ids.append(data_item_id)
