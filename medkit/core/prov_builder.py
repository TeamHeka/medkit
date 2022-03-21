from __future__ import annotations

__all__ = ["ProvBuilder"]

from typing import List

from medkit.core.prov_graph import ProvGraph, ProvNode


class ProvBuilder:
    def __init__(self):
        self.graph: ProvGraph = ProvGraph()

    def add_prov(
        self,
        data_item_id: str,
        operation_id: str,
        source_ids: List[str],
    ):
        assert not self.graph.has_node(
            data_item_id
        ), f"Provenance of data item with id {data_item_id} was already added"

        node = ProvNode(data_item_id, operation_id, source_ids)
        self.graph.add_node(node)

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
