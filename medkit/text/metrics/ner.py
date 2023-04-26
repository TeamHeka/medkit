__all__ = ["SeqEvalEvaluator", "SeqEvalMetricsComputer"]

import dataclasses
import itertools
from typing import Any, Dict, List, Optional
from typing_extensions import Literal

from seqeval.metrics import accuracy_score, classification_report
from seqeval.scheme import BILOU, IOB2

from medkit.core.text import TextDocument, Entity
from medkit.text.ner import hf_tokenization_utils
from medkit.training.utils import BatchData

SPECIAL_TAG_ID_HF: int = -100


def _compute_seqeval_from_dict(
    all_data: Dict[str, List[any]],
    scheme: Literal["bilou", "iob2"],
    mode,
    return_metrics_by_label,
) -> Dict[str, float]:
    """Compute seqeval metrics using a dictionary of NER tags"""

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

    The evaluator converts the set of entites and documents to tags before compute the metric.
    It supports two schemes, IOB2 (a BIO scheme) and BILOU. The IOB2 scheme tags the Beginning,
    the Inside and the Outside text of a entity. The BILOU scheme tags the Beginning,
    the Inside and the Last tokens of multi-token entity as well as Unit-length entity.

    For more information about IOB schemes, refer to the `Wikipedia page <https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)>`_

    (TODO: cite in documentation, add example here or in `compute`)
    Hiroki Nakayama. (2018). seqeval: A Python framework for sequence labeling evaluation.

    .. hint::
        If **tokenizer** is not defined, the evaluator tokenizes the text by character.
        This may generate a lot of tokens with large documents and may affect execution time.
        You can use a fast tokenizer from HuggingFace, i.e. : bert tokenizer

        >>> from transformers import AutoTokenizer
        >>> tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased", use_fast=True)
    """

    def __init__(
        self,
        tokenizer: Optional[Any] = None,
        tagging_scheme: Literal["bilou", "iob2"] = "bilou",
        return_metrics_by_label: bool = True,
    ):
        """
        Parameters
        ----------
        tokenizer:
            Optional tokenizer to convert text into tokens.
            If not provided, a tokenizer per-character is created.
        tagging_scheme:
            Scheme for tagging the tokens, it can be `bilou` or `iob2`
        return_metrics_by_label:
            If `True`, return the metrics by label in the output dictionnary.
            If `False`, only return overall metrics
        """
        if tokenizer is None:
            tokenizer = _CharacterTokenizer()

        self.tokenizer = tokenizer
        self.tagging_scheme = tagging_scheme
        self.return_metrics_by_label = return_metrics_by_label

        # internal configuration for seqeval, 'bilou' only works with 'strict' mode
        self._scheme = BILOU if self.tagging_scheme == "bilou" else IOB2
        self._mode = "strict" if self.tagging_scheme == "bilou" else None

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
            text_encoding = self.tokenizer(document.text).encodings[0]
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

        scores = _compute_seqeval_from_dict(
            all_data=all_data,
            mode=self._mode,
            scheme=self._scheme,
            return_metrics_by_label=self.return_metrics_by_label,
        )
        return scores


class _CharacterTokenizer:
    """A simple implementation of a per-character tokenizer.
    The outputs use the same structure as a HuggingFace tokenizer,
    this guarantees compatibility with tokenization methods.

    Example
    -------
    >>> tokenizer = CharacterTokenizer()
    >>> tokenizer("hello")
    BatchEncoding(encodings=[Encoding(tokens=['h', 'e', 'l', 'l', 'o'])])
    """

    def __call__(self, text: str):
        return _BatchEncoding([_Encoding(tokens=[c for c in text])])


@dataclasses.dataclass
class _Encoding:
    tokens: List[str]

    def char_to_token(self, idx):
        return idx

    def __len__(self):
        return len(self.tokens)


@dataclasses.dataclass
class _BatchEncoding:
    encodings: List[_Encoding]

    def __len__(self):
        return len(self.encodings)

    def __getitem__(self, idx):
        return self.encodings[idx]


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
            If `True`, return the metrics by label in the output dictionnary.
            If `False`, only return overall metrics
        """
        self.id_to_label = id_to_label
        self.return_metrics_by_label = return_metrics_by_label

        # internal configuration for seqeval,
        # 'bilou' only works with 'strict' mode
        self._scheme = BILOU if tagging_scheme == "bilou" else IOB2
        self._mode = "strict" if tagging_scheme == "bilou" else None

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
        scores = _compute_seqeval_from_dict(
            all_data=all_data,
            mode=self._mode,
            scheme=self._scheme,
            return_metrics_by_label=self.return_metrics_by_label,
        )
        return scores
