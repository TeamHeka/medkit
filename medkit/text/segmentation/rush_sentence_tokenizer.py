from __future__ import annotations

__all__ = ["RushSentenceTokenizer"]

import dataclasses
from pathlib import Path
import re
from typing import Iterator, List, Optional, Union, TYPE_CHECKING

from PyRuSH import RuSH

from medkit.core import Origin, ProcessingDescription, RuleBasedAnnotator
from medkit.core.text import TextBoundAnnotation, TextDocument
import medkit.core.text.span as span_utils

if TYPE_CHECKING:
    from medkit.core.document import Collection
    from medkit.core.text.span import AnySpan


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    input_label = TextDocument.RAW_TEXT_LABEL
    output_label = "SENTENCE"
    path_to_rules = None
    keep_newlines = True


_PATH_TO_DEFAULT_RULES = (
    Path(__file__).parent / "rush_sentence_tokenizer_default_rules.tsv"
)


class RushSentenceTokenizer(RuleBasedAnnotator):
    """Sentence segmentation annotator based on PyRuSH."""

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def __init__(
        self,
        input_label: str = DefaultConfig.input_label,
        output_label: str = DefaultConfig.output_label,
        path_to_rules: Union[str, Path] = DefaultConfig.path_to_rules,
        keep_newlines: bool = DefaultConfig.keep_newlines,
        proc_id: Optional[str] = None,
    ):
        """
        Instantiate the RuSH tokenizer

        Parameters
        ----------
        input_label:
            The input label of the annotations to use as input.
            Default: "RAW_TEXT" (cf. DefaultConfig)
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
        self.input_label = input_label
        self.output_label = output_label
        if path_to_rules is None:
            path_to_rules = _PATH_TO_DEFAULT_RULES
        self._rush = RuSH(str(path_to_rules))
        self.keep_newlines = keep_newlines

        config = dict(
            input_label=input_label,
            output_label=output_label,
            path_to_rules=path_to_rules,
            keep_newlines=keep_newlines,
        )

        self._description = ProcessingDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )

    def annotate(self, collection: Collection):
        """
        Process the collection of documents for extracting sentences.
        Sentences are represented by text bound annotations
        in each text document of the collection.

        Parameters
        ----------
        collection: Collection
            Collection of documents
        """
        for doc in collection.documents:
            if isinstance(doc, TextDocument):
                self.annotate_document(doc)

    def annotate_document(self, document: TextDocument):
        """
        Process a document for extracting sentences.
        Sentences are represented by text bound annotations
        in each text document of the collection.

        Parameters
        ----------
        document: TextDocument
            The text document to process
        """
        # Retrieve annotations on which we want to apply sentence segmentation
        # e.g., section
        input_ann_ids = document.segments.get(self.input_label, None)
        if input_ann_ids:
            input_anns = [
                document.get_annotation_by_id(ann_id) for ann_id in input_ann_ids
            ]
            output_anns = self._process_doc_annotations(input_anns)
            for ann in output_anns:
                # Add each sentence as annotation in doc
                document.add_annotation(ann)

    def _process_doc_annotations(
        self, annotations: List[TextBoundAnnotation]
    ) -> Iterator[TextBoundAnnotation]:
        """
        Create an annotation for each sentence detected in input annotations

        Parameters
        ----------
        annotations:
            List of input annotations to process

        Yields
        ------
        TextBoundAnnotation:
            Created annotation representing a token
        """
        for ann in annotations:
            sentences = self._extract_sentences_and_spans(ann)
            for text, spans in sentences:
                new_annotation = TextBoundAnnotation(
                    origin=Origin(processing_id=self.description.id, ann_ids=[ann.id]),
                    label=self.output_label,
                    spans=spans,
                    text=text,
                )
                yield new_annotation

    def _extract_sentences_and_spans(
        self, text_annotation: TextBoundAnnotation
    ) -> Iterator[(str, List[AnySpan])]:
        rush_spans = self._rush.segToSentenceSpans(text_annotation.text)
        for rush_span in rush_spans:
            text, spans = span_utils.extract(
                text=text_annotation.text,
                spans=text_annotation.spans,
                ranges=[(rush_span.begin, rush_span.end)],
            )

            if not self.keep_newlines:
                ranges = [m.span() for m in re.finditer(r"\n", text)]
                replacements = " " * len(ranges)
                text, spans = span_utils.replace(text, spans, ranges, replacements)

            yield text, spans

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)
