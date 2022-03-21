from __future__ import annotations

__all__ = ["RushSentenceTokenizer"]

import dataclasses
from pathlib import Path
import re
from typing import Iterator, List, Optional, Union

from PyRuSH import RuSH

from medkit.core import Origin, OperationDescription, RuleBasedAnnotator, generate_id
from medkit.core.text import Segment, span_utils


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label = "SENTENCE"
    path_to_rules = None
    keep_newlines = True


_PATH_TO_DEFAULT_RULES = (
    Path(__file__).parent / "rush_sentence_tokenizer_default_rules.tsv"
)


class RushSentenceTokenizer(RuleBasedAnnotator):
    """Sentence segmentation annotator based on PyRuSH."""

    def __init__(
        self,
        output_label: str = DefaultConfig.output_label,
        path_to_rules: Union[str, Path] = DefaultConfig.path_to_rules,
        keep_newlines: bool = DefaultConfig.keep_newlines,
        proc_id: Optional[str] = None,
    ):
        """
        Instantiate the RuSH tokenizer

        Parameters
        ----------
        output_label:
            The output label of the created annotations.
            Default: "SENTENCE" (cf.DefaultConfig)
        path_to_rules:
            Path to csv or tsv file to provide to PyRuSH. If none provided,
            "rush_tokenizer_default_rules.tsv" will be used
            (corresponds to the "conf/rush_rules.tsv" in the PyRush repo)
        keep_newlines:
            With the default rules, newline chars are not used to split
            sentences, therefore a sentence maybe contain one or more newline chars.
            If `keep_newlines` is False, newlines will be replaced by spaces.
        proc_id:
            Identifier of the tokenizer
        """

        if proc_id is None:
            proc_id = generate_id()
        if path_to_rules is None:
            path_to_rules = _PATH_TO_DEFAULT_RULES

        self.id: str = proc_id
        self.output_label = output_label
        self.path_to_rules = path_to_rules
        self.keep_newlines = keep_newlines
        self._rush = RuSH(str(path_to_rules))

    @property
    def description(self) -> OperationDescription:
        config = dict(
            output_label=self.output_label,
            path_to_rules=self.path_to_rules,
            keep_newlines=self.keep_newlines,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def process(self, segments: List[Segment]) -> List[Segment]:
        """
        Return sentences detected in `segments`.

        Parameters
        ----------
        segments:
            List of segments into which to look for sentences

        Returns
        -------
        List[Segments]:
            Sentences segments found in `segments`
        """
        return [
            sentence
            for segment in segments
            for sentence in self._find_sentences_in_segment(segment)
        ]

    def _find_sentences_in_segment(self, segment: Segment) -> Iterator[Segment]:
        rush_spans = self._rush.segToSentenceSpans(segment.text)
        for rush_span in rush_spans:
            text, spans = span_utils.extract(
                text=segment.text,
                spans=segment.spans,
                ranges=[(rush_span.begin, rush_span.end)],
            )

            if not self.keep_newlines:
                ranges = [m.span() for m in re.finditer(r"\n", text)]
                replacements = " " * len(ranges)
                text, spans = span_utils.replace(text, spans, ranges, replacements)

            sentence = Segment(
                origin=Origin(operation_id=self.id, ann_ids=[segment.id]),
                label=self.output_label,
                spans=spans,
                text=text,
            )
            yield sentence

    @classmethod
    def from_description(cls, description: OperationDescription):
        return cls(proc_id=description.id, **description.config)
