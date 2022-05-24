from __future__ import annotations

__all__ = ["HFTranslator"]

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import torch
import transformers
from transformers import TranslationPipeline, BertModel, BertTokenizerFast

from medkit.core import (
    OperationDescription,
    ProvBuilder,
    generate_id,
)

from medkit.core.text import Segment, ModifiedSpan, span_utils


class HFTranslator:
    """Translator based on a Hugging Face transformers model

    For segment given in input, a translated segment will be returned.
    The spans of the translated segment are "aligned" to the original segment.
    An alignment model is used to find matches between translated words and
    original words, and for each of these matches a `ModifiedSpan` is created, referencing
    the original span in the original text.

    Segment given in input should not contain more than one sentence, because only the 1st
    sentence will be translated and the others will be discarded (this might vary with the model).
    The formatting will not be preserved.
    """

    def __init__(
        self,
        output_label: str = "translation",
        translation_model: str = "Helsinki-NLP/opus-mt-fr-en",
        alignment_model: str = "bert-base-multilingual-cased",
        alignment_layer: int = 8,
        alignment_threshold: float = 1e-3,
        proc_id: str = None,
    ):
        """Instantiate the translator

        Parameters
        ----------
        output_label:
            The label of the created annotations
        translation_model:
            Name of the translation model on the Hugging Face models hub. Must be a model compatible
            with the TranslationPipeline transformers class.
        alignment_model:
            Name of the alignment model on the Hugging Face models hub. Must be a multilingual BERT model
            compatible with the BertModel transformers class.
        alignment_layer:
            Index of the layer in the alignment model that contains the token embeddings
            (the original and translated embedding will be. compared)
        alignment_threshold:
            Threshold value used to decide if embeddings are similar enough to be aligned

        proc_id:
            Identifier of the translator
        """
        if proc_id is None:
            proc_id = generate_id()

        self.id: str = proc_id
        self.output_label: str = output_label
        self.translation_model: str = translation_model
        self.alignment_model: str = alignment_model
        self.alignment_layer: int = alignment_layer
        self.alignment_threshold: float = alignment_threshold

        self._translation_pipeline: TranslationPipeline = transformers.pipeline(
            model=self.translation_model
        )
        self._aligner: _Aligner = _Aligner(
            model=self.alignment_model,
            layer_index=self.alignment_layer,
            threshold=self.alignment_threshold,
        )

        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        config = dict(
            output_label=self.output_label,
            translation_model=self.translation_model,
            alignment_model=self.alignment_model,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def run(self, segments: List[Segment]) -> List[Segment]:
        """
        Translate short segments (can't contain multiple sentences)

        Parameters
        ----------
        segments:
            List of segments to translate

        Returns
        -------
        List[Segments]:
            Translated segments (with spans referring to words in original text, for translated
            words that have been aligned to original words)
        """
        return [self._translate_segment(s) for s in segments]

    def _translate_segment(self, segment: Segment) -> Segment:
        # TODO translate batches of segments instead of one segment at a time?
        translated_text = self._translation_pipeline(segment.text)[0][
            "translation_text"
        ]
        translated_spans = self._get_translated_spans(
            translated_text, segment.text, segment.spans
        )

        translated_segment = Segment(
            label=self.output_label,
            spans=translated_spans,
            text=translated_text,
        )

        if self._prov_builder is not None:
            self._prov_builder.add_prov(
                translated_segment, self.description, source_data_items=[segment]
            )

        return translated_segment

    def _get_translated_spans(self, translated_text, original_text, original_spans):
        """Compute spans for translated segments, making translated words reference words
        in original text through ModifiedSpans when possible"""

        # compute words alignment
        alignment = self._aligner.align(translated_text, original_text)

        # build translated spans, which will contains:
        # - ModifiedSpans with no replacement_spans, for non-aligned parts of translated text
        #   (ie gaps between aligned words, plus head and tail)
        # - ModifiedSpans with replacement_spans pointing to original word(s) for aligned words
        #   in translated text
        # - plain Spans pointing to original word(s) for aligned words, when the translated word
        #   is identical to the original word
        translated_spans = []
        current_char = 0
        for translated_range, original_ranges in alignment.items():
            translated_start, translated_end = translated_range
            translated_sub_text = translated_text[translated_start:translated_end]

            # handle gaps between aligned sub texts
            if current_char < translated_start:
                translated_spans.append(
                    ModifiedSpan(translated_start - current_char, replaced_spans=[])
                )

            # extract spans corresponding to sub text in original text
            original_sub_text, original_sub_text_spans = span_utils.extract(
                original_text, original_spans, original_ranges
            )
            if translated_sub_text == original_sub_text:
                # if translation sub text is identical to original,
                # we can use the original spans
                translated_spans += original_sub_text_spans
            else:
                # otherwise create modified span pointing to original spans
                length = translated_end - translated_start
                translated_spans.append(
                    ModifiedSpan(length, replaced_spans=original_sub_text_spans)
                )

            current_char = translated_end

        # handle trail
        if current_char < len(translated_text):
            translated_spans.append(
                ModifiedSpan(len(translated_text) - current_char, replaced_spans=[])
            )

        assert sum(s.length for s in translated_spans) == len(translated_text)
        return translated_spans

    @classmethod
    def from_description(cls, description: OperationDescription):
        return cls(proc_id=description.id, **description.config)


class _Aligner:
    def __init__(
        self,
        model: str = "bert-base-multilingual-cased",
        layer_index: int = 8,
        threshold: float = 1e-3,
    ):
        self._model = BertModel.from_pretrained(model)
        self._layer_index = layer_index
        self._threshold: float = threshold
        self._tokenizer = BertTokenizerFast.from_pretrained(model)

    def align(
        self, source_text: str, target_text: str
    ) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        """Compute word alignments between two texts in different languages.

        Parameters
        ----------
        source_text:
            The text to align from (typically the translated text)
        target_text:
            The text to align to (typically the original text)

        Returns
        -------
        Dict[Tuple[int, int], List[Tuple[int, int]]]:
            The alignments between characters ranges.
            For each entry in the dict, the key is the character range of a word in `source_text`,
            and the value is a list of one or more character ranges in `target_text`,
            corresponding to one or more words (a word in the source text might be aligned to
            several words in the target text).
        """
        # preprocess
        source_encoding = self._encode_text(source_text)
        target_encoding = self._encode_text(target_text)
        words_by_token_source = self._get_words_by_token(source_encoding)
        words_by_token_target = self._get_words_by_token(target_encoding)

        # align tokens
        self._model.eval()
        with torch.no_grad():
            # extract source embeddings
            in_source = source_encoding["input_ids"]
            out_source = self._model(in_source, output_hidden_states=True)
            out_source = out_source[2][self._layer_index][0, 1:-1]
            # extract target embeddings
            in_target = target_encoding["input_ids"]
            out_target = self._model(in_target, output_hidden_states=True)
            out_target = out_target[2][self._layer_index][0, 1:-1]
            # compute similarity between embeddings forward and backwards
            dot_prod = torch.matmul(out_source, out_target.transpose(-1, -2))
            softmax_source_target = torch.nn.Softmax(dim=-1)(dot_prod)
            softmax_target_source = torch.nn.Softmax(dim=-2)(dot_prod)
            # flag as aligned where similarities are greater than threshold
            softmax_inter = (softmax_source_target > self._threshold) * (
                softmax_target_source > self._threshold
            )
            tokens_alignments = torch.nonzero(softmax_inter, as_tuple=False)

        # align word spans (build word alignments from token alignments, and take word spans)
        alignments = defaultdict(list)
        for source_token, target_token in tokens_alignments:
            source_word = words_by_token_source[source_token]
            source_range = tuple(source_encoding.word_to_chars(source_word))
            target_word = words_by_token_target[target_token]
            target_range = tuple(target_encoding.word_to_chars(target_word))
            if target_range not in alignments[source_range]:
                alignments[source_range].append(target_range)

        # sort target ranges (tokens_alignments is sorted on 1st column (source)
        # but not necessarily on 2d column (target), ie. it is not monotonic)
        for target_ranges in alignments.values():
            target_ranges.sort()

        return alignments

    def _encode_text(self, text):
        """Return a BatchEncoder instance
        (useful for converting token back to words and CharSpans,
        but requires a TokenizerFast)"""
        encoding = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self._tokenizer.model_max_length,
        )
        return encoding

    def _get_words_by_token(self, encoding):
        """Return a list containing the word index for each token
        (allows to map back each token to its corresponding word)"""
        nb_words = 0
        words_by_token = []
        prev_word = None
        for word in encoding.word_ids():
            if word is None:
                continue
            if word != prev_word:
                nb_words += 1
                prev_word = word
            words_by_token.append(nb_words - 1)
        return words_by_token
