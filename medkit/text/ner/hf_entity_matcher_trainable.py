"""
This module needs extra-dependencies not installed as core dependencies of medkit.
To install them, use `pip install medkit-lib[hf-entity-matcher]`.
"""
__all__ = ["HFEntityMatcherTrainable"]
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from typing_extensions import Literal

import torch
import transformers

from medkit.core.text import Entity, TextDocument
from medkit.text.ner import hf_tokenization_utils
from medkit.tools import hf_utils
from medkit.training.utils import BatchData

logger = logging.getLogger(__name__)


class HFEntityMatcherTrainable:
    """
    Trainable entity matcher based on HuggingFace transformers model
    Any token classification model from the HuggingFace hub can be used
    (for instance "samrawal/bert-base-uncased_clinical-ner").
    """

    def __init__(
        self,
        model_name_or_path: Union[str, Path],
        labels: List[str],
        tagging_scheme: Literal["bilou", "iob2"],
        tag_subtokens: bool = False,
        tokenizer_max_length: Optional[int] = None,
        device: int = -1,
    ):
        """
        Parameters
        ----------
        model_name_or_path:
            Name (on the HuggingFace models hub) or path of the NER model. Must be a model compatible
            with the `TokenClassification` transformers class.
        labels:
            List of labels to detect
        tagging_scheme:
            Tagging scheme to use in the segment-entities preprocessing and label mapping definition.
        tag_subtokens:
            Whether tag subtokens in a word. PreTrained models require a tokenization step.
            If any word of the segment is not in the vocabulary of the tokenizer used by the PreTrained model,
            the word is split into subtokens.
            It is recommended to only tag the first subtoken of a word. However, it is possible to tag all subtokens
            by setting this value to `True`. It could influence the time and results of fine-tunning.
        tokenizer_max_length:
            Optional max length for the tokenizer, by default the `model_max_length` will be used.
        device:
            Device to use for the transformer model. Follows the HuggingFace convention
            (-1 for "cpu" and device number for gpu, for instance 0 for "cuda:0").
        """

        valid_model = hf_utils.check_model_for_task_HF(
            model_name_or_path, "token-classification"
        )
        if not valid_model:
            raise ValueError(
                f"Model {model_name_or_path} is not associated to a"
                " token-classification/ner task and cannot be used with"
                " HFEntityMatcher"
            )

        self.model_name_or_path = model_name_or_path
        self.tagging_scheme = tagging_scheme
        self.tag_subtokens = tag_subtokens
        self.tokenizer_max_length = tokenizer_max_length
        self.model_config = self._get_valid_model_config(labels)

        # update labels mapping using the configuration
        self.label_to_id = self.model_config.label2id
        self.id_to_label = self.model_config.id2label

        # load tokenizer and model using the model path
        self.load(self.model_name_or_path)
        self.device = torch.device("cpu" if device < 0 else f"cuda:{device}")
        self._model.to(self.device)

    def configure_optimizer(self, lr: float) -> torch.optim.Optimizer:
        # todo: group_params optimizer_parameters = [{}]
        optimizer_parameters = self._model.parameters()
        optimizer = torch.optim.AdamW(optimizer_parameters, lr=lr)
        return optimizer

    def preprocess(self, data_item: TextDocument) -> Dict[str, Any]:
        text_encoding = self._encode_text(data_item.text)
        entities: List[Entity] = data_item.anns.entities

        tags = hf_tokenization_utils.transform_entities_to_tags(
            entities=entities,
            text_encoding=text_encoding,
            tagging_scheme=self.tagging_scheme,
        )
        tags_ids = hf_tokenization_utils.align_and_map_tokens_with_tags(
            text_encoding=text_encoding,
            tags=tags,
            tag_to_id=self.label_to_id,
            map_sub_tokens=self.tag_subtokens,
        )

        model_input = {}
        model_input["input_ids"] = text_encoding.ids
        model_input["attention_masks"] = text_encoding.attention_mask
        model_input["labels"] = tags_ids

        return model_input

    def _encode_text(self, text):
        """Return a EncodingFast instance"""
        text_tokenized = self._tokenizer(
            text,
            padding="max_length",
            max_length=self.tokenizer_max_length,
            truncation=True,
            return_special_tokens_mask=True,
        )
        encoding = text_tokenized.encodings[0]
        return encoding

    def collate(self, batch: List[Dict[str, Any]]) -> BatchData:
        input_ids, attention_masks, labels = [], [], []
        for input_data in batch:
            input_ids.append(input_data["input_ids"])
            attention_masks.append(input_data["attention_masks"])
            labels.append(input_data["labels"])

        collated_batch = BatchData(
            {
                "input_ids": torch.LongTensor(input_ids),
                "attention_masks": torch.LongTensor(attention_masks),
                "labels": torch.LongTensor(labels),
            }
        )
        return collated_batch

    def forward(
        self,
        input_batch: BatchData,
        return_loss: bool,
        eval_mode: bool,
    ) -> Tuple[BatchData, Optional[torch.Tensor]]:
        if eval_mode:
            self._model.eval()
        else:
            self._model.train()

        model_output = self._model(
            input_ids=input_batch["input_ids"],
            attention_mask=input_batch["attention_masks"],
            labels=input_batch["labels"],
        )
        loss = model_output["loss"] if return_loss else None
        return BatchData(logits=model_output["logits"]), loss

    def save(self, path: Union[str, Path]):
        state_dict = self._model.state_dict()
        self._model.save_pretrained(path, state_dict=state_dict)
        self._tokenizer.save_pretrained(path)

    def load(self, path: Union[str, Path]):
        tokenizer = transformers.AutoTokenizer.from_pretrained(path, use_fast=True)

        if not isinstance(tokenizer, transformers.PreTrainedTokenizerFast):
            raise ValueError(
                "This operation only works with model that have a fast tokenizer. Check"
                " the hugging face documentation to find the required tokenizer"
            )

        model = transformers.AutoModelForTokenClassification.from_pretrained(
            path,
            config=self.model_config,
            ignore_mismatched_sizes=True,
        )

        self._tokenizer = tokenizer
        self._model = model

    def _get_valid_model_config(self, labels: List[str]):
        """Return a config file with the correct mapping of labels"""
        # get possible tags from labels list
        label_to_id = hf_tokenization_utils.convert_labels_to_tags(
            labels=labels, tagging_scheme=self.tagging_scheme
        )
        nb_labels = len(label_to_id)

        # load configuration with the correct number of NER labels
        config = transformers.AutoConfig.from_pretrained(
            self.model_name_or_path, num_labels=nb_labels
        )

        # If the model has the same labels, we kept the original mapping
        # Easier finetunning
        if sorted(config.label2id.keys()) != sorted(label_to_id.keys()):
            logger.warning(
                f"""The operation model seems to have different labels.
            PreTrained with labels: {sorted(config.label2id.keys())}, new labels
            {sorted(label_to_id.keys())}. Ignoring the model labels as result."""
            )
            config.label2id = {label: idx for idx, label in label_to_id.items()}
            config.id2label = {idx: label for idx, label in label_to_id.items()}

        return config
