from __future__ import annotations

__all__ = ["Normalizer", "NormalizerRule"]

import re
from typing import List, Optional, NamedTuple

from medkit.core import generate_id, OperationDescription, ProvBuilder
from medkit.core.text import Segment, span_utils


class NormalizerRule(NamedTuple):
    pattern_to_replace: str
    new_text: str


class Normalizer:
    """
    Generic normalizer to be used as pre-processing module

    This module is a non-destructive module allowing to replace selected characters
    with the wanted characters.
    It respects the span modification by creating a new text-bound annotation containing
    the span modification information from input text.
    """

    def __init__(
        self,
        output_label: str,
        rules: List[NormalizerRule] = None,
        proc_id: str = None,
    ):
        """
        TODO: change default output_label
        Parameters
        ----------
        output_label
            The output label of the created annotations
        rules
            The list of normalization rules
        proc_id
            Identifier of the pre-processing module
        """
        if proc_id is None:
            proc_id = generate_id()
        self.id = proc_id
        self.output_label = output_label
        if rules is None:
            rules = []
        self.rules = rules

        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        config = dict(
            output_label=self.output_label,
            rules=self.rules,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def run(self, segments: List[Segment]) -> List[Segment]:
        """
        Run the module on a list of segments provided as input
        and returns a new list of segments

        Parameters
        ----------
        segments
            List of segments to normalize

        Returns
        -------
        List[Segment]
            List of normalized segments
        """
        return [
            norm_segment
            for segment in segments
            for norm_segment in self._normalize_segment_text(segment)
        ]

    def _normalize_segment_text(self, segment: Segment):
        regex_rules = ["(" + rule.pattern_to_replace + ")" for rule in self.rules]
        regex_rule = r"|".join(regex_rules)
        pattern = re.compile(regex_rule)

        ranges = []
        replacement_texts = []

        for match in pattern.finditer(segment.text):
            ranges.append(match.span())
            for index in range(len(self.rules)):
                if match.groups()[index] is not None:
                    replacement_texts.append(self.rules[index].new_text)

        new_text, new_spans = span_utils.replace(
            text=segment.text,
            spans=segment.spans,
            ranges=ranges,
            replacement_texts=replacement_texts,
        )

        normalized_text = Segment(
            label=self.output_label, spans=new_spans, text=new_text
        )

        if self._prov_builder is not None:
            self._prov_builder.add_prov(
                normalized_text, self.description, source_data_items=[segment]
            )

        yield normalized_text

    @classmethod
    def from_description(cls, description: OperationDescription):
        return cls(proc_id=description.id, **description.config)
