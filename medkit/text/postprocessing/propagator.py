__all__ = ["AttributePropagator"]

from typing import Dict, List, Optional
from intervaltree import IntervalTree
from medkit.core.annotation import Attribute
from medkit.core.text import Segment, span_utils, ContextOperation


class AttributePropagator(ContextOperation):
    """Annotator used to propagate attributes from a segment to a nested segment."""

    def __init__(
        self,
        attr_labels: List[str],
        op_id: Optional[str] = None,
    ):
        """Instantiate the attribute propagator

        Parameters
        ----------
        attr_labels:
            List of the labels of the attributes to propagate
        op_id:
            Identifier of the detector
        """
        self.attr_labels = attr_labels
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

    def run(self, source_segments: List[Segment], target_segments: List[Segment]):
        """Add attributes from a source segment to all nested segments

        Parameters
        ----------
        source_segments:
            List of segments with attributes to propagate
        target_segments:
            List of segments target
        """
        nested = self._compute_nested_segments(source_segments, target_segments)

        for parent, children in nested.items():
            attrs_to_propagate = [
                attr
                for label in self.attr_labels
                for attr in parent.get_attrs_by_label(label)
            ]

            if len(attrs_to_propagate) == 0:
                continue

            # create a new attr in target from the source attr
            for attr in attrs_to_propagate:
                for child in children:
                    self._propagate_attr(attr=attr, target=child)

    def _compute_nested_segments(
        self, source_segments, target_segments: Segment
    ) -> IntervalTree:
        tree = IntervalTree()
        for segment in target_segments:
            normalized_spans = span_utils.normalize_spans(segment.spans)

            if not normalized_spans:
                continue

            tree.addi(
                normalized_spans[0].start,
                normalized_spans[-1].end,
                data=segment,
            )
        return self._find_nested(tree, source_segments)

    def _find_nested(
        self, tree: IntervalTree, source_segments: List[Segment]
    ) -> Dict[Segment, List[Segment]]:
        nested = {}
        for segment in source_segments:
            normalized_spans = span_utils.normalize_spans(segment.spans)
            start, end = normalized_spans[0].start, normalized_spans[-1].end
            nested[segment] = [child.data for child in tree.overlap(start, end)]
        return nested

    def _propagate_attr(self, attr: Attribute, target: Segment):
        target_attr = Attribute(
            label=attr.label, value=attr.value, metadata=attr.metadata
        )

        target.add_attr(target_attr)

        if self._prov_tracer is not None:
            self._prov_tracer.add_prov(
                target_attr, self.description, source_data_items=[attr]
            )
