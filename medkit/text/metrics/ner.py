__all__ = ["SeqEvalMetricsComputer", "SeqEvalEvaluator"]

import itertools
from typing import Dict, List, Literal

from seqeval.metrics import accuracy_score, classification_report
from seqeval.scheme import BILOU, IOB2

from medkit.core.text import TextDocument, Entity
from medkit.text.ner import hf_tokenization_utils

from medkit.training.utils import BatchData

SPECIAL_TAG_ID_HF: int = -100


class _SeqEvalInternalComputer:
    """Generic computer for seqeval metrics"""

    @staticmethod
    def compute(
        all_data: Dict[str, List[any]], scheme, mode, return_entity_metrics
    ) -> Dict[str, float]:
        # extract and format data from all_data
        y_true_all = all_data.get("y_true", [])
        y_pred_all = all_data.get("y_pred", [])

        if not len(y_true_all) or not len(y_pred_all):
            raise ValueError("'all_data' has no required data to compute the metric")

        size_last_dim = len(y_pred_all[0][0][0])
        if size_last_dim > 1:
            # dim of all_data is (nb_batches,n,m), metric requires (nb_batches*n,nb_batches*m)
            y_true_all = list(itertools.chain(*y_true_all))
            y_pred_all = list(itertools.chain(*y_pred_all))

        report = classification_report(
            y_true=y_true_all,
            y_pred=y_pred_all,
            scheme=scheme,
            output_dict=True,
            zero_division=0,
            mode=mode,
        )
        # add overall_metrics
        scores = {f"overall_{key}": value for key, value in report["micro avg"].items()}
        scores["overall_acc"] = accuracy_score(y_pred=y_pred_all, y_true=y_true_all)

        if return_entity_metrics:
            ent_keys = [key for key in report.keys() if not key.endswith("avg")]
            for ent_key in ent_keys:
                for metric_key, metric_value in report[ent_key].items():
                    scores[f"{ent_key}_{metric_key}"] = metric_value

        return scores


class SeqEvalMetricsComputer:
    """Implementation of :class:`~medkit.training.MetricsComputer` that use `seqeval`
    to compute sequence metrics in NER operations.

    Could be used with
    :class:`~medkit.training.Trainer>` to control the training of NER trainable operations.
    """

    def __init__(
        self,
        id_to_label: Dict[int, str],
        tagging_scheme: Literal["bilou", "iob2"] = "bilou",
        return_entity_metrics: bool = True,
    ):
        self.id_to_label = id_to_label
        self.scheme = BILOU if tagging_scheme == "bilou" else IOB2
        # bilou only works in strict mode
        self._mode = "strict" if tagging_scheme == "bilou" else None
        self.return_entity_metrics = return_entity_metrics

    def prepare_batch(
        self, model_output: BatchData, input_batch: BatchData
    ) -> Dict[str, List[List[str]]]:
        predictions_ids = (
            model_output["logits"].argmax(dim=-1).detach().to("cpu").numpy()
        )
        references_ids = input_batch["labels"].detach().to("cpu").numpy()

        # ignore special tokens
        mask_special_tokens = references_ids != SPECIAL_TAG_ID_HF

        batch_true_tags = [
            [self.id_to_label[tag] for tag in ref[mask_special_tokens[i]]]
            for i, ref in enumerate(references_ids)
        ]
        batch_pred_tags = [
            [self.id_to_label[tag] for tag in pred[mask_special_tokens[i]]]
            for i, pred in enumerate(predictions_ids)
        ]
        return {"y_true": batch_true_tags, "y_pred": batch_pred_tags}

    def compute(self, all_data: Dict[str, List[any]]) -> Dict[str, float]:
        scores = _SeqEvalInternalComputer.compute(
            all_data=all_data,
            mode=self._mode,
            scheme=self.scheme,
            return_entity_metrics=self.return_entity_metrics,
        )
        return scores


class SeqEvalEvaluator:
    """Evaluator that use `seqeval` to compute sequence metrics in NER operations."""

    def __init__(
        self,
        tokenizer,
        tagging_scheme: Literal["bilou", "iob2"] = "bilou",
        return_entity_metrics: bool = True,
    ):
        self.tokenizer = tokenizer
        self.tagging_scheme = tagging_scheme
        self.scheme = BILOU if self.tagging_scheme == "bilou" else IOB2
        # bilou only works in strict mode
        self._mode = "strict" if self.tagging_scheme == "bilou" else None
        self.return_entity_metrics = return_entity_metrics

    def compute(
        self, documents: List[TextDocument], predicted_entities: List[List[Entity]]
    ) -> Dict[str, float]:
        true_tags_all, pred_tags_all = [], []

        for document, pred_entities in zip(documents, predicted_entities):
            text_encoding = self._encode_text(document.text)
            true_entities = document.anns.entities

            true_tags_all.append(
                hf_tokenization_utils.transform_entities_to_tags(
                    text_encoding=text_encoding,
                    entities=true_entities,
                    tagging_scheme=self.tagging_scheme,
                )
            )
            pred_tags_all.append(
                hf_tokenization_utils.transform_entities_to_tags(
                    text_encoding=text_encoding,
                    entities=pred_entities,
                    tagging_scheme=self.tagging_scheme,
                )
            )

        all_data = {"y_true": true_tags_all, "y_pred": pred_tags_all}

        scores = _SeqEvalInternalComputer.compute(
            all_data=all_data,
            mode=self._mode,
            scheme=self.scheme,
            return_entity_metrics=self.return_entity_metrics,
        )
        return scores

    def _encode_text(self, text):
        """Return a EncodingFast instance"""
        text_tokenized = self.tokenizer(
            text,
            truncation=True,
            return_special_tokens_mask=True,
        )
        encoding = text_tokenized.encodings[0]
        return encoding
