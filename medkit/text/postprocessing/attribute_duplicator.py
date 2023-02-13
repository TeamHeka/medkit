__all__ = ["AttributeDuplicator"]

from typing import List, Optional, Tuple
from intervaltree import IntervalTree
from medkit.core import Attribute, Operation
from medkit.core.text import Segment, span_utils


class AttributeDuplicator(Operation):
    """Annotator to copy attributes from a source segment to its nested segments.
    For each attribute to be duplicated, a new attribute is created in the nested segment
    """

    def __init__(
        self,
        attr_labels: List[str],
        uid: Optional[str] = None,
    ):
        """Instantiate the attribute duplicator

        Parameters
        ----------
        attr_labels:
            Labels of the attributes to copy
        uid:
            Identifier of the annotator
        """
        self.attr_labels = attr_labels
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

    def run(self, source_segments: List[Segment], target_segments: List[Segment]):
        """Add attributes from source segments to all nested segments.
        The nested segments are chosen among the `target_segments` based on their spans.

        Parameters
        ----------
        source_segments:
            List of segments with attributes to copy
        target_segments:
            List of segments target
        """
        nested = self._compute_nested_segments(source_segments, target_segments)

        for parent, children in nested:
            attrs_to_copy = [
                attr
                for label in self.attr_labels
                for attr in parent.attrs.get(label=label)
            ]

            # create a new attr in target from the source attr
            for attr in attrs_to_copy:
                for child in children:
                    self._duplicate_attr(attr=attr, target=child)

    def _compute_nested_segments(
        self, source_segments: List[Segment], target_segments: List[Segment]
    ) -> List[Tuple[Segment, List[Segment]]]:
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
    ) -> List[Tuple[Segment, List[Segment]]]:
        nested = []
        for parent in source_segments:
            normalized_spans = span_utils.normalize_spans(parent.spans)

            if not normalized_spans:
                continue

            start, end = normalized_spans[0].start, normalized_spans[-1].end
            children = [child.data for child in tree.overlap(start, end)]
            nested.append((parent, children))
        return nested

    def _duplicate_attr(self, attr: Attribute, target: Segment):
        target_attr = attr.copy()
        target.attrs.add(target_attr)

        if self._prov_tracer is not None:
            self._prov_tracer.add_prov(
                target_attr, self.description, source_data_items=[attr]
            )
