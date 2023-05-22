__all__ = ["SeqEvalEvaluator", "SeqEvalMetricsComputer"]

from typing import Any, Dict, List, Optional
from typing_extensions import Literal

from seqeval.metrics import accuracy_score, classification_report
from seqeval.scheme import BILOU, IOB2

from medkit.core.text import TextDocument, Entity, span_utils
from medkit.text.ner import hf_tokenization_utils
from medkit.training.utils import BatchData


def _compute_seqeval_from_dict(
    y_true_all: List[List[str]],
    y_pred_all: List[List[str]],
    tagging_scheme: Literal["bilou", "iob2"],
    return_metrics_by_label,
) -> Dict[str, float]:
    """Compute seqeval metrics using preprocessed data"""

    # internal configuration for seqeval
    # 'bilou' only works with 'strict' mode
    scheme = BILOU if tagging_scheme == "bilou" else IOB2
    mode = "strict" if tagging_scheme == "bilou" else None

    # returns precision, recall, F1 score for each class.
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

    if return_metrics_by_label:
        ent_keys = [key for key in report.keys() if not key.endswith("avg")]
        for ent_key in ent_keys:
            for metric_key, metric_value in report[ent_key].items():
                scores[f"{ent_key}_{metric_key}"] = metric_value

    return scores


class SeqEvalEvaluator:
    """Evaluator to compute the performance of labeling tasks such as
    named entity recognition. This evaluator compares TextDocuments of reference
    with its predicted annotations and returns a dictionary of metrics.

    The evaluator converts the set of entities and documents to tags before compute the metric.
    It supports two schemes, IOB2 (a BIO scheme) and BILOU. The IOB2 scheme tags the Beginning,
    the Inside and the Outside text of a entity. The BILOU scheme tags the Beginning,
    the Inside and the Last tokens of multi-token entity as well as Unit-length entity.

    For more information about IOB schemes, refer to the `Wikipedia page <https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)>`_

    .. hint::
        If **tokenizer** is not defined, the evaluator tokenizes the text by character.
        This may generate a lot of tokens with large documents and may affect execution time.
        You can use a fast tokenizer from HuggingFace, i.e. : bert tokenizer

        >>> from transformers import AutoTokenizer
        >>> tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased", use_fast=True)
    """

    def __init__(
        self,
        tagging_scheme: Literal["bilou", "iob2"] = "bilou",
        return_metrics_by_label: bool = True,
        tokenizer: Optional[Any] = None,
    ):
        """
        Parameters
        ----------
        tagging_scheme:
            Scheme for tagging the tokens, it can be `bilou` or `iob2`
        return_metrics_by_label:
            If `True`, return the metrics by label in the output dictionary.
            If `False`, only return overall metrics
        tokenizer:
            Optional Fast Tokenizer to convert text into tokens.
            If not provided, the text is tokenized by character.
        """
        self.tokenizer = tokenizer
        self.tagging_scheme = tagging_scheme
        self.return_metrics_by_label = return_metrics_by_label

    def compute(
        self, documents: List[TextDocument], predicted_entities: List[List[Entity]]
    ) -> Dict[str, float]:
        """Compute metrics of entity matching giving predictions.

        Parameters
        ----------
        documents:
            Text documents containing entities of reference
        predicted_entities:
            List of predicted entities by document

        Returns
        -------
        Dict[str, float]:
            A dictionary with overall and per type metrics if required. The metrics included are:
            accuracy, precision, recall and F1 score.
        """
        true_tags_all, pred_tags_all = [], []

        for document, pred_entities in zip(documents, predicted_entities):
            text = document.text
            true_entities = document.anns.entities

            true_tags_all.append(
                self._tag_text_with_entities(text=text, entities=true_entities)
            )
            pred_tags_all.append(
                self._tag_text_with_entities(text=text, entities=pred_entities)
            )
        scores = _compute_seqeval_from_dict(
            y_true_all=true_tags_all,
            y_pred_all=pred_tags_all,
            tagging_scheme=self.tagging_scheme,
            return_metrics_by_label=self.return_metrics_by_label,
        )
        return scores

    def _tag_text_with_entities(self, text: str, entities: List[Entity]):
        if self.tokenizer is not None:
            # tags tokenized text, creates one tag per token
            text_encoding = self.tokenizer(text).encodings[0]
            tags = hf_tokenization_utils.transform_entities_to_tags(
                text_encoding=text_encoding,
                entities=entities,
                tagging_scheme=self.tagging_scheme,
            )
            return tags

        # tags untokenized text, create one tag per character
        tags = ["O"] * len(text)
        for ent in entities:
            label = ent.label
            ent_spans = span_utils.normalize_spans(ent.spans)
            start_char = ent_spans[0].start
            end_char = ent_spans[-1].end
            chars_entity = list(range(start_char, end_char))

            if not chars_entity:
                continue

            entity_tags = hf_tokenization_utils.create_entity_tags(
                nb_tags=len(chars_entity),
                label=label,
                tagging_scheme=self.tagging_scheme,
            )
            for token_idx, tag in zip(chars_entity, entity_tags):
                tags[token_idx] = tag

        return tags


class SeqEvalMetricsComputer:
    """An implementation of :class:`~medkit.training.MetricsComputer` using seqeval
    to compute metrics in the training of named-entity recognition components.

    The metrics computer can be used with a :class:`~medkit.training.Trainer`
    """

    def __init__(
        self,
        id_to_label: Dict[int, str],
        tagging_scheme: Literal["bilou", "iob2"] = "bilou",
        return_metrics_by_label: bool = True,
    ):
        """
        id_to_label:
            Mapping integer value to label, it should be the same used in preprocess
        tagging_scheme:
            Scheme used for tagging the tokens, it can be `bilou` or `iob2`
        return_metrics_by_label:
            If `True`, return the metrics by label in the output dictionary.
            If `False`, only return overall metrics
        """
        self.id_to_label = id_to_label
        self.tagging_scheme = tagging_scheme
        self.return_metrics_by_label = return_metrics_by_label

    def prepare_batch(
        self, model_output: BatchData, input_batch: BatchData
    ) -> Dict[str, List[List[str]]]:
        """Prepare a batch of tensors to compute the metric

        Parameters
        ----------
        model_output:
            A batch data including the `logits` predicted by the model
        input_batch:
            A batch data including the `labels` of reference

        Returns
        -------
        Dict[str, List[List[str]]]
            A dictionary with the true and predicted tags representation of a batch data
        """
        predictions_ids = (
            model_output["logits"].argmax(dim=-1).detach().to("cpu").numpy()
        )
        references_ids = input_batch["labels"].detach().to("cpu").numpy()
        # ignore special tokens
        mask_special_tokens = references_ids != hf_tokenization_utils.SPECIAL_TAG_ID_HF

        batch_true_tags = [
            [self.id_to_label[tag] for tag in ref[mask]]
            for ref, mask in zip(references_ids, mask_special_tokens)
        ]

        batch_pred_tags = [
            [self.id_to_label[tag] for tag in pred[mask]]
            for pred, mask in zip(predictions_ids, mask_special_tokens)
        ]

        return {"y_true": batch_true_tags, "y_pred": batch_pred_tags}

    def compute(self, all_data: Dict[str, List[Any]]) -> Dict[str, float]:
        """Compute metrics using the tag representation collected by batches
        during the training/evaluation loop.

        Parameters
        ----------
        all_data:
            A dictionary with the true and predicted tags collected by batches

        Returns
        -------
        Dict[str, float]:
            A dictionary with overall and per label metrics if required. The metrics
            included are : accuracy, precision, recall and F1 score.

        """
        # extract and format data from all_data
        y_true_all = all_data.get("y_true", [])
        y_pred_all = all_data.get("y_pred", [])

        scores = _compute_seqeval_from_dict(
            y_pred_all=y_pred_all,
            y_true_all=y_true_all,
            tagging_scheme=self.tagging_scheme,
            return_metrics_by_label=self.return_metrics_by_label,
        )
        return scores
