"""
This module needs extra-dependencies not installed as core dependencies of medkit.
To install them, use `pip install medkit-lib[rush-sentence-tokenizer]`.
"""

from __future__ import annotations

__all__ = ["RushSentenceTokenizer"]

import dataclasses
from pathlib import Path
import re
from typing import Iterator, List, Optional, Union

from PyRuSH import RuSH

from medkit.core.text import Segment, SegmentationOperation, span_utils


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label = "SENTENCE"
    path_to_rules = None
    keep_newlines = True


_PATH_TO_DEFAULT_RULES = (
    Path(__file__).parent / "rush_sentence_tokenizer_default_rules.tsv"
)


class RushSentenceTokenizer(SegmentationOperation):
    """Sentence segmentation annotator based on PyRuSH."""

    def __init__(
        self,
        output_label: str = DefaultConfig.output_label,
        path_to_rules: Union[str, Path] = DefaultConfig.path_to_rules,
        keep_newlines: bool = DefaultConfig.keep_newlines,
        uid: Optional[str] = None,
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
        uid:
            Identifier of the tokenizer
        """
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        if path_to_rules is None:
            path_to_rules = _PATH_TO_DEFAULT_RULES

        self.output_label = output_label
        self.path_to_rules = path_to_rules
        self.keep_newlines = keep_newlines
        self._rush = RuSH(str(path_to_rules))

    def run(self, segments: List[Segment]) -> List[Segment]:
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
                label=self.output_label,
                spans=spans,
                text=text,
            )

            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    sentence, self.description, source_data_items=[segment]
                )

            yield sentence
