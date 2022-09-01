from __future__ import annotations

__all__ = ["AttributePropagator"]

from typing import List, Optional
from intervaltree import IntervalTree

from medkit.core.text import Segment, span_utils, ContextOperation
from medkit.core import Attribute


class AttributePropagator(ContextOperation):
    """Annotator used to propagate attributes from a segment to a nested segment."""

    def __init__(
        self,
        attr_labels: List[str],
        max_gap_length: int = 3,
        op_id: Optional[str] = None,
    ):
        """Instantiate the attribute propagator

        Parameters
        ----------
        attr_labels:
            List of the labels of the attributes to propagate
        max_gap_length:
            When cleaning up gaps in spans, spans around gaps smaller than `max_gap_length`
            will be merged.
            Cf :func:`~medkit.core.text.span_utils.clean_up_gaps_in_normalized_spans()`.
        op_id:
            Identifier of the detector
        """

        self.attr_labels = attr_labels
        self.max_gap_length = max_gap_length

        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

    def run(self, segments: List[Segment]):
        """Add attributes from a segment to all nested segments

        Parameters
        ----------
        segments:
            List of segments to be included in the propagation operation (sources and targets)
        """

        t = IntervalTree()

        for segment in segments:
            normalized_spans = span_utils.normalize_spans(segment.spans)
            if not normalized_spans:
                continue

            # merge close spans

            print(normalized_spans)
            t.addi(
                min([s.start for s in normalized_spans]),
                max([s.end for s in normalized_spans]),
                data=segment,
            )

        nested = t.find_nested()

        for parent in nested.keys():
            attrs_to_propagate = [
                attr
                for attr in parent.data.get_attrs()
                if attr.label in self.attr_labels
            ]

            if len(attrs_to_propagate) == 0:
                continue

            for attr in attrs_to_propagate:
                for child in nested[parent]:
                    self._propagate_attribute(target=child.data, attr=attr)

    def _propagate_attribute(self, target: Segment, attr: Attribute):
        target_attr = Attribute(
            label=attr.label, value=attr.value, metadata=attr.metadata
        )

        if self._prov_tracer is not None:
            self._prov_tracer.add_prov(
                target_attr, self.description, source_data_items=[attr]
            )

        target.add_attr(target_attr)
