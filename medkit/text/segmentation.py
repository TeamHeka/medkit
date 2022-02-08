import dataclasses
import re
from typing import Iterator, List, Union, TYPE_CHECKING

from medkit.core.processing import ProcessingDescription, RuleBasedAnnotator
from medkit.core.text import Entity, TextDocument
import medkit.core.text.span as span_utils

if TYPE_CHECKING:
    from medkit.core.document import Collection
    from medkit.core.text.span import Span, ModifiedSpan


@dataclasses.dataclass
class SentenceTokenizerConfig:
    input_label: str
    output_label: str = "SENTENCE"
    punct_chars: List[str] = dataclasses.field(
        default_factory=lambda: ["\r", "\n", ".", ";", "?", "!"]
    )
    keep_punct: bool = False


class SentenceTokenizer(RuleBasedAnnotator):
    """Sentence segmentation annotator based on end punctuation rules"""

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def __init__(self, proc_id=None, config=None):

        self._description = ProcessingDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )
        config = SentenceTokenizerConfig(config)
        self.input_label = config.input_label
        self.output_label = config.output_label
        self.punct_chars = config.punct_chars
        self.keep_punct = config.keep_punct

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
                # Retrieve annotations on which we want to apply sentence segmentation
                # e.g., section
                input_anns = doc.entities.get(self.input_label, None)
                if input_anns:
                    output_anns = self._process_doc_annotations(input_anns)
                    for ann in output_anns:
                        # Add each sentence as annotation in doc
                        doc.add_annotation(ann)

    def _process_doc_annotations(self, annotations: List[Entity]) -> Iterator[Entity]:
        """
        Create an entity for each sentence detected in input annotations

        Parameters
        ----------
        annotations: List[Entity]
            List of input annotations to process
        Returns
        -------
        Iterator[Entity]:
            An iterator on each created entity representing a sentence
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
        pattern = re.compile("%s" % regex_rule)

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
                text_annotation.text, text_annotation.spans, [(start, end)]
            )
            yield text, spans
