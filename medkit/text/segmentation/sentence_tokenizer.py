from __future__ import annotations

__all__ = ["SentenceTokenizer"]

import dataclasses
import re
from typing import Iterator, List, Optional, Tuple

from medkit.core import Origin, OperationDescription, RuleBasedAnnotator, generate_id
from medkit.core.text import Segment, span_utils


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label = "SENTENCE"
    punct_chars = ("\r", "\n", ".", ";", "?", "!")
    keep_punct = False


class SentenceTokenizer(RuleBasedAnnotator):
    """Sentence segmentation annotator based on end punctuation rules"""

    def __init__(
        self,
        output_label: str = DefaultConfig.output_label,
        punct_chars: Tuple[str] = DefaultConfig.punct_chars,
        keep_punct: bool = DefaultConfig.keep_punct,
        proc_id: Optional[str] = None,
    ):
        """
        Instantiate the sentence tokenizer

        Parameters
        ----------
        output_label: str, Optional
            The output label of the created annotations.
            Default: "SENTENCE" (cf.DefaultConfig)
        punct_chars: Tuple[str], Optional
            The set of characters corresponding to end punctuations.
            Default: ("\r", "\n", ".", ";", "?", "!") (cf. DefaultConfig)
        keep_punct: bool, Optional
            If True, the end punctuations are kept in the detected sentence.
            If False, the sentence text does not include the end punctuations
            Default: False (cf. DefaultConfig)
        proc_id: str, Optional
            Identifier of the tokenizer
        """
        if proc_id is None:
            proc_id = generate_id()

        self.id: str = proc_id
        self.output_label = output_label
        self.punct_chars = punct_chars
        self.keep_punct = keep_punct

    @property
    def description(self) -> OperationDescription:
        config = dict(
            output_label=self.output_label,
            punct_chars=self.punct_chars,
            keep_punct=self.keep_punct,
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
        regex_rule = (
            "(?P<blanks> *)"  # Blanks at the beginning of the sentence
            + "(?P<sentence>.+?)"  # Sentence to detect
            + "(?P<punctuation>["  # End punctuation (may be repeated)
            + "".join(self.punct_chars)
            + "]+)"
        )
        pattern = re.compile(regex_rule)

        for match in pattern.finditer(segment.text):
            # Ignore empty sentences
            if len(match.group("sentence").strip()) == 0:
                continue

            start = match.start("sentence")
            end = match.end("punctuation") if self.keep_punct else match.end("sentence")

            # Extract raw span list from regex match ranges
            text, spans = span_utils.extract(
                text=segment.text,
                spans=segment.spans,
                ranges=[(start, end)],
            )

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
