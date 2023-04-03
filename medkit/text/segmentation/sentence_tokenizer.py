from __future__ import annotations

__all__ = ["SentenceTokenizer"]

import dataclasses
import re
from typing import Iterator, List, Optional, Tuple

from medkit.core.text import Segment, SegmentationOperation, span_utils


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label = "SENTENCE"
    punct_chars = (".", ";", "?", "!")
    keep_punct = False
    split_on_newlines = True


class SentenceTokenizer(SegmentationOperation):
    """Sentence segmentation annotator based on end punctuation rules"""

    def __init__(
        self,
        output_label: str = DefaultConfig.output_label,
        punct_chars: Tuple[str] = DefaultConfig.punct_chars,
        keep_punct: bool = DefaultConfig.keep_punct,
        split_on_newlines: bool = DefaultConfig.split_on_newlines,
        uid: Optional[str] = None,
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
        split_on_newlines:
            Whether to consider that newlines characters are sentence boundaries or not.
        uid: str, Optional
            Identifier of the tokenizer
        """
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        self.output_label = output_label
        self.punct_chars = punct_chars
        self.keep_punct = keep_punct
        self.split_on_newlines = split_on_newlines

        # pre-compile patterns
        self._newline_pattern = re.compile(
            r" *(?P<content>[^\n\r]+) *(?P<separator>[\n\r]+|$)"
        )
        punct_string = re.escape("".join(self.punct_chars))
        self._punct_pattern = re.compile(
            rf" *(?P<content>[^{punct_string}]+) *(?P<separator>[{punct_string}]+|$)"
        )

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
        # split on newlines (discarding newline chars) then split each line on punct chars
        if self.split_on_newlines:
            for line_start, line_end in self._split_text(
                segment.text, self._newline_pattern, keep_separator=False
            ):
                sub_text = segment.text[line_start:line_end]
                for sub_start, sub_end in self._split_text(
                    sub_text, self._punct_pattern, keep_separator=self.keep_punct
                ):
                    start = line_start + sub_start
                    end = line_start + sub_end
                    yield self._build_sentence(segment, range=(start, end))
        # or split directly on punct chars
        else:
            for start, end in self._split_text(
                segment.text, self._punct_pattern, keep_separator=self.keep_punct
            ):
                yield self._build_sentence(segment, range=(start, end))

    @staticmethod
    def _split_text(
        text: str, pattern: re.Pattern, keep_separator: bool
    ) -> Iterator[Tuple[int, int]]:
        for match in pattern.finditer(text):
            start = match.start("content")
            end = match.end("separator") if keep_separator else match.end("content")
            has_letters = re.search(r"\w", text[start:end])
            if end > start and has_letters:
                yield start, end

    def _build_sentence(
        self, source_segment: Segment, range: Tuple[int, int]
    ) -> Segment:
        text, spans = span_utils.extract(
            text=source_segment.text,
            spans=source_segment.spans,
            ranges=[range],
        )

        sentence = Segment(
            label=self.output_label,
            spans=spans,
            text=text,
        )

        if self._prov_tracer is not None:
            self._prov_tracer.add_prov(
                sentence, self.description, source_data_items=[source_segment]
            )

        return sentence
