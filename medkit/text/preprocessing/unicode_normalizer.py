from __future__ import annotations

__all__ = ["UnicodeNormalizer"]

import dataclasses
import re

import unidecode

from typing import List, Optional

from medkit.core import (
    OperationDescription,
    ProvBuilder,
    generate_id,
)

from medkit.core.text import Segment, span_utils

UNICODE_TO_REPLACE = [
    "\u00C6",  # Æ
    "\u00E6",  # æ
    "\u0152",  # Œ
    "\u0153",  # œ
]


@dataclasses.dataclass(frozen=True)
class DefaultConfig:  # TODO (#44): to remove when input key will be used as label
    output_label = "NORMALIZED_TEXT"


class UnicodeNormalizer:
    """
    Unicode normalizer pre-processing annotation module

    This module is a non-destructive module allowing to convert special unicode
    character (e.g., œ) to the closest ascii characters.
    It respects the span modification by creating a new text-bound annotation containing
    the span modification information from input text.

    For the time being, only 'ae' and 'oe' ligatures (upper/lowercase) are supported.
    """

    def __init__(
        self, output_label: str = DefaultConfig.output_label, proc_id: str = None
    ):
        """
        Instantiate the unicode normalizer.

        Parameters
        ----------
        output_label
            The output label of the created annotations.
            Default: "NORMALIZED_TEXT" (cf.DefaultConfig)  # TODO: cf. #44
        proc_id
            Identifier of the pre-processing module
        """
        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self.output_label = output_label

        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        config = dict(
            output_label=self.output_label,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def run(self, segments: List[Segment]) -> List[Segment]:
        """
        Run the module on a list of segments provided as input
        and returns a new list of segments.

        Parameters
        ----------
        segments
            List of segments to normalize

        Returns
        -------
        List[Segments]:
            List of normalized segments.
        """
        return [
            norm_segment
            for segment in segments
            for norm_segment in self._normalize_segment_text(segment)
        ]

    def _normalize_segment_text(self, segment: Segment):
        regex_rule = "(?P<unicode>" + "|".join(UNICODE_TO_REPLACE) + ")"
        pattern = re.compile(regex_rule)

        ranges = []
        replacement_texts = []

        for match in pattern.finditer(segment.text):
            ranges.append(match.span())
            replacement_texts.append(unidecode.unidecode(match.group("unicode")))

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
