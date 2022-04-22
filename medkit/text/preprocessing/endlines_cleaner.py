__all__ = ["EndlinesCleaner"]

import dataclasses


from typing import List, Optional

from medkit.core import (
    OperationDescription,
    ProvBuilder,
    generate_id,
)

from medkit.core.text import utils
from medkit.core.text import Segment


# TBD: default config
_FR_CIVIL_TITLES = ["M", "Mme", "Mlle", "Mr", "Pr", "Dr", "Mde"]
_FR_PREPOSITIONS = [
    "de",
    "par",
    "le",
    "du",
    "la",
    "les",
    "des",
    "un",
    "une",
    "ou",
    "pour",
    "avec",
]


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label = "CLEAN_TEXT"
    keep_endlines = False
    handle_parentheses_eds = True


class EndlinesCleaner:
    """
    Endlines pre-processing annotation module

    This module is a non-destructive module allowing to remove and clean selected points
    and newlines characters. It respects the span modification by creating a new text-bound annotation containing
    the span modification information from input text.

    """

    def __init__(
        self,
        output_label: str = DefaultConfig.output_label,
        keep_endlines: bool = DefaultConfig.keep_endlines,
        handle_parentheses_eds: bool = DefaultConfig.handle_parentheses_eds,
        proc_id: str = None,
    ):
        """
        Instantiate the endlines handler.

        Parameters
        ----------
        output_label
            The output label of the created annotations.
            Default: "CLEAN_TEXT" (cf.DefaultConfig)
        keep_endlines:


        handle_parentheses_eds:
        proc_id
            Identifier of the pre-processing module
        """
        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self.output_label = output_label
        self.keep_endlines = keep_endlines
        self.handle_parentheses_eds = handle_parentheses_eds

        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        config = dict(
            output_label=self.output_label,
            keep_endlines=self.keep_endlines,
            handle_parentheses_eds=self.handle_parentheses_eds,
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
            List of cleaned segments.
        """
        return [
            norm_segment
            for segment in segments
            for norm_segment in self._clean_segment_text(segment)
        ]

    def _clean_segment_text(self, segment: Segment):
        # handle points characters
        # replace points after civil titles defined by a list
        new_text, new_spans = utils.replace_point_after_keywords(
            text=segment.text,
            spans=segment.spans,
            keywords=_FR_CIVIL_TITLES,
            strict=True,
        )
        new_text, new_spans = utils.replace_point_in_uppercase(new_text, new_spans)
        new_text, new_spans = utils.replace_point_in_numbers(new_text, new_spans)
        # replace points after prepositions
        new_text, new_spans = utils.replace_point_after_keywords(
            text=new_text,
            spans=new_spans,
            keywords=_FR_PREPOSITIONS,
            strict=False,
        )

        # handle newline character
        new_text, new_spans = utils.clean_multiple_whitespaces_in_sentence(
            new_text, new_spans
        )
        new_text, new_spans = utils.clean_newline_character(
            text=new_text, spans=new_spans, keep_endlines=self.keep_endlines
        )

        # handle parentheses
        if self.handle_parentheses_eds:
            new_text, new_spans = utils.clean_parentheses_eds(new_text, new_spans)

        # create ann with the clean text
        clean_text = Segment(label=self.output_label, spans=new_spans, text=new_text)

        if self._prov_builder is not None:
            self._prov_builder.add_prov(
                clean_text, self.description, source_data_items=[segment]
            )

        yield clean_text

    @classmethod
    def from_description(cls, description: OperationDescription):
        return cls(proc_id=description.id, **description.config)
