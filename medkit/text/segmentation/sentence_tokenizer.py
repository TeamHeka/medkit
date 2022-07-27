from __future__ import annotations

__all__ = ["SentenceTokenizer"]

import dataclasses
import re
from typing import Iterator, List, Optional, Tuple

from medkit.core.text import Segment, SegmentationOperation, span_utils


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label = "SENTENCE"
    punct_chars = ("\r", "\n", ".", ";", "?", "!")
    keep_punct = False


class SentenceTokenizer(SegmentationOperation):
    """Sentence segmentation annotator based on end punctuation rules"""

    def __init__(
        self,
        output_label: str = DefaultConfig.output_label,
        punct_chars: Tuple[str] = DefaultConfig.punct_chars,
        keep_punct: bool = DefaultConfig.keep_punct,
        op_id: Optional[str] = None,
    ):
        """
        Instantiate the sentence tokenizer

        Parameters
        ----------
        output_label: str, Optional
            The output label of the created annotations.
        punct_chars: Tuple[str], Optional
            The set of characters corresponding to end punctuations.
        keep_punct: bool, Optional
            If True, the end punctuations are kept in the detected sentence.
            If False, the sentence text does not include the end punctuations.
        op_id: str, Optional
            Identifier of the tokenizer
        """
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        self.output_label = output_label
        self.punct_chars = punct_chars
        self.keep_punct = keep_punct

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
        regex_rule = (
            "(?P<blanks> *)"  # Blanks at the beginning of the sentence
            + "(?P<sentence>.+?)"  # Sentence to detect
            + "(?P<punctuation>["  # End punctuation (may be repeated)
            + "".join(self.punct_chars)
            + "]+|$)"  # including potential last sentence without punct
        )
        pattern = re.compile(regex_rule, flags=re.DOTALL)

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
                label=self.output_label,
                spans=spans,
                text=text,
            )

            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    sentence, self.description, source_data_items=[segment]
                )

            yield sentence
