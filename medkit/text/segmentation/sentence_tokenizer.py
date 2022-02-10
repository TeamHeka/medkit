from __future__ import annotations

__all__ = []

import dataclasses
import re
from typing import Iterator, List, Tuple, Union, TYPE_CHECKING

from medkit.core.processing import ProcessingDescription, RuleBasedAnnotator
from medkit.core.text import Entity, TextDocument
import medkit.core.text.span as span_utils

if TYPE_CHECKING:
    from medkit.core.document import Collection
    from medkit.core.text.span import Span, ModifiedSpan


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    input_label = "RAW_TEXT"
    output_label = "SENTENCE"
    punct_chars = ("\r", "\n", ".", ";", "?", "!")
    keep_punct = False


class SentenceTokenizer(RuleBasedAnnotator):
    """Sentence segmentation annotator based on end punctuation rules"""

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def __init__(
        self,
        input_label: str = DefaultConfig.input_label,
        output_label: str = DefaultConfig.output_label,
        punct_chars: Tuple[str] = DefaultConfig.punct_chars,
        keep_punct: bool = DefaultConfig.keep_punct,
        proc_id=None,
    ):
        """
        Instantiate the sentence tokenizer

        Parameters
        ----------
        input_label: str, Optional
            The input label of the annotations to use as input.
            Default: "RAW_TEXT" (cf. DefaultConfig)
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
        self.input_label = input_label
        self.output_label = output_label
        self.punct_chars = punct_chars
        self.keep_punct = keep_punct

        config = dict(
            input_label=input_label,
            output_label=output_label,
            punct_chars=punct_chars,
            keep_punct=keep_punct,
        )

        self._description = ProcessingDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )

    def annotate(self, collection: Collection):
        """
        Process the collection of documents for extracting sentences.
        Sentences are represented by annotations in each text document of the
        collection.

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
        Sentences are represented by annotations in the text document

        Parameters
        ----------
        document: TextDocument
            The text document to process

        Returns
        -------

        """
        # Retrieve annotations on which we want to apply sentence segmentation
        # e.g., section
        input_ann_ids = document.entities.get(self.input_label, None)
        if input_ann_ids:
            input_anns = [
                document.get_annotation_by_id(ann_id) for ann_id in input_ann_ids
            ]
            output_anns = self._process_doc_annotations(input_anns)
            for ann in output_anns:
                # Add each sentence as annotation in doc
                document.add_annotation(ann)

    def _process_doc_annotations(self, annotations: List[Entity]) -> Iterator[Entity]:
        """
        Create an entity for each sentence detected in input annotations

        Parameters
        ----------
        annotations: List[Entity]
            List of input annotations to process
        Yields
        -------
        Entity:
            Created entity representing a sentence
        """
        for ann in annotations:
            sentences = self._extract_sentences_and_spans(ann)
            for text, spans in sentences:
                new_annotation = Entity(
                    origin_id=self.description.id,
                    label=self.output_label,
                    spans=spans,
                    text=text,
                )
                yield new_annotation

    def _extract_sentences_and_spans(
        self, text_annotation: Entity
    ) -> Iterator[(str, List[Union[Span, ModifiedSpan]])]:
        regex_rule = (
            "(?P<blanks> *)"  # Blanks at the beginning of the sentence
            + "(?P<sentence>.+?)"  # Sentence to detect
            + "(?P<punctuation>["  # End punctuation (may be repeated)
            + "".join(self.punct_chars)
            + "]+)"
        )
        pattern = re.compile(regex_rule)

        for match in pattern.finditer(text_annotation.text):
            sentence = match.group("sentence")
            if len(sentence.strip()) == 0:  # Ignore empty sentences
                continue
            start = match.start("sentence")
            if self.keep_punct:
                sentence += match.group("punctuation")
                end = match.end("punctuation")
            else:
                end = match.end("sentence")

            # Extract raw span list from regex match ranges
            text, spans = span_utils.extract(
                text=text_annotation.text,
                spans=text_annotation.spans,
                ranges=[(start, end)],
            )
            yield text, spans

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)
