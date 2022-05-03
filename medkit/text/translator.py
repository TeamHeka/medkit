from __future__ import annotations

__all__ = ["Translator"]

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import torch
import transformers

from medkit.core import (
    OperationDescription,
    ProvBuilder,
    generate_id,
)

from medkit.core.text import Segment, ModifiedSpan, span_utils


class Translator:
    def __init__(
        self,
        translation_model: str = "Helsinki-NLP/opus-mt-fr-en",
        alignment_model: str = "bert-base-multilingual-cased",
        output_label: str = "translation",
        proc_id: str = None,
    ):
        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self.output_label = output_label
        self.translation_model = translation_model
        self.alignment_model = alignment_model

        self._translation_pipeline = transformers.pipeline(
            "translation_en_to_fr", model=self.translation_model
        )
        self._aligner = _Aligner(alignment_model=self.alignment_model)

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
        return [self._translate_segment(segment) for segment in segments]

    def _translate_segment(self, segment: Segment) -> Segment:
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
        alignment = self._aligner.align(translated_text, original_text)

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
    def __init__(self, alignment_model: str = "bert-base-multilingual-cased"):
        self._model = transformers.BertModel.from_pretrained(alignment_model)
        self._tokenizer = transformers.BertTokenizerFast.from_pretrained(
            alignment_model
        )

    def align(
        self, source_text: str, target_text: str
    ) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        # preprocess
        source_encoding = self._encode_text(source_text)
        target_encoding = self._encode_text(target_text)
        words_by_token_source = self._get_words_by_token(source_encoding)
        words_by_token_target = self._get_words_by_token(target_encoding)

        # align tokens
        align_layer = 8
        threshold = 1e-3
        self._model.eval()
        with torch.no_grad():
            in_source = source_encoding["input_ids"]
            out_source = self._model(in_source, output_hidden_states=True)
            out_source = out_source[2][align_layer][0, 1:-1]
            in_target = target_encoding["input_ids"]
            out_target = self._model(in_target, output_hidden_states=True)
            out_target = out_target[2][align_layer][0, 1:-1]

            dot_prod = torch.matmul(out_source, out_target.transpose(-1, -2))

            softmax_source_target = torch.nn.Softmax(dim=-1)(dot_prod)
            softmax_target_source = torch.nn.Softmax(dim=-2)(dot_prod)

            softmax_inter = (softmax_source_target > threshold) * (
                softmax_target_source > threshold
            )
        tokens_alignments = torch.nonzero(softmax_inter, as_tuple=False)

        # align word spans
        alignments = defaultdict(list)
        for source_token, target_token in tokens_alignments:
            source_word = words_by_token_source[source_token]
            source_range = tuple(source_encoding.word_to_chars(source_word))
            target_word = words_by_token_target[target_token]
            target_range = tuple(target_encoding.word_to_chars(target_word))
            if target_range not in alignments[source_range]:
                alignments[source_range].append(target_range)

        # sort target ranges (tokens_alignments is sorted on 1st column (source)
        # but not necessarily on 2d column (target) since later tokens in a source word
        # might refer to earlier target tokens)
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
        (allows to map back each token to its corresponding word"""
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
