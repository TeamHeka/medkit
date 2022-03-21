from __future__ import annotations

__all__ = ["ProvGraph", "ProvNode"]

import dataclasses
from typing import Dict, List, Optional


@dataclasses.dataclass
class ProvNode:
    data_item_id: str
    operation_id: Optional[str]
    source_ids: List[str]
    derived_ids: List[str] = dataclasses.field(default_factory=list)


class ProvGraph:
    def __init__(self, nodes: Optional[List[ProvNode]] = None):
        if nodes is None:
            nodes = []

        self._nodes_by_id: Dict[str, ProvNode] = {n.data_item_id: n for n in nodes}

    def get_nodes(self) -> List[ProvNode]:
        return list(self._nodes_by_id.values())

    def get_node(self, data_item_id: str) -> ProvNode:
        return self._nodes_by_id[data_item_id]

    def add_node(self, node: ProvNode):
        assert node.data_item_id not in self._nodes_by_id
        self._nodes_by_id[node.data_item_id] = node

    def has_node(self, data_item_id: str) -> bool:
        return data_item_id in self._nodes_by_id

    def check_sanity(self):
        for node_id, node in self._nodes_by_id.items():
            if node.source_ids and node.operation_id is None:
                raise Exception(
                    f"Node with id {node_id} has source ids but no operation"
                )
            for source_id in node.source_ids:
                source_node = self._nodes_by_id.get(source_id)
                if source_node is None:
                    raise Exception(
                        f"Source id {source_id} in node with id {node_id} has no"
                        " corresponding node"
                    )
                if node_id not in source_node.derived_ids:
                    raise Exception(
                        f"Node with id {node_id} has source item with id"
                        f" {source_id} but reciprocate derivation link does not exists"
                    )
            for derived_id in node.derived_ids:
                derived_node = self._nodes_by_id.get(derived_id)
                if derived_node is None:
                    raise Exception(
                        f"Derived id {derived_id} in node with id {node_id} has no"
                        " corresponding node"
                    )
                if node_id not in derived_node.source_ids:
                    raise Exception(
                        f"Node with id {node_id} has derived item with id"
                        f" {derived_id} but reciprocate source link does not exists"
                    )
