from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import transformers

from medkit.core import IdentifiableDataItem
from medkit.core.text.annotation import Entity, Segment
from medkit.training.utils import BatchData
from medkit.training.utils_tokenization_HF import (
    tag_tokens_with_labels,
    transform_entities_to_labels,
)


class HFEntityMatcherTrainable:
    """
    Trainable entity matcher based on HuggingFace transformers model
    Any token classification model from the HuggingFace hub can be used
    (for instance "samrawal/bert-base-uncased_clinical-ner").
    """

    def __init__(
        self,
        model_name_or_path: Union[str, Path],
        label_to_id: Dict[str, int],
        use_bilou_scheme: bool = True,
        max_length: int = 512,
        tag_all_labels=True,
        device: int = -1,
        cache_dir: Optional[Union[str, Path]] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        model_name_or_path:
            Name (on the HuggingFace models hub) or path of the NER model. Must be a model compatible
            with the `TokenClassification` transformers class.
        device:
            Device to use for the transformer model. Follows the HuggingFace convention
            (-1 for "cpu" and device number for gpu, for instance 0 for "cuda:0").
        cache_dir:
            Directory where to store downloaded models. If not set, the default
            HuggingFace cache dir is used.
        name:
            Name describing the matcher (defaults to the class name).
        uid:
            Identifier of the matcher.
        """

        self.model_name_or_path = model_name_or_path
        self.cache_dir = cache_dir

        if isinstance(self.model_name_or_path, str):
            task = transformers.pipelines.get_task(self.model_name_or_path)
            if task != "token-classification":
                raise ValueError(
                    f"Model {self.model_name_or_path} is not associated to a"
                    " token-classification/ner task and cannot be used with"
                    " HFEntityMatcher"
                )
        # define mapping
        self.label_to_id = label_to_id
        self.id_to_label = {i: label for label, i in label_to_id.items()}
        self.use_bilou_scheme = use_bilou_scheme
        self.max_length = max_length
        self.tag_all_labels = tag_all_labels

        # load tokenizer and model using the model path
        self.load(self.model_name_or_path)
        self.device = torch.device("cpu" if device < 0 else f"cuda:{device}")
        self._model.to(self.device)

    def configure_optimizer(self, lr: float) -> torch.optim.Optimizer:
        # todo: group_params optimizer_parameters = [{}]
        optimizer_parameters = self._model.parameters()
        optimizer = torch.optim.AdamW(optimizer_parameters, lr=lr)
        return optimizer

    def preprocess(
        self, data_item: IdentifiableDataItem, inference_mode: bool
    ) -> Dict[str, Any]:
        segment: Segment = data_item[0]
        entities: List[Entity] = data_item[1]

        text_encoding = self._encode_text(segment.text)
        tags = []

        if not inference_mode:
            labels = transform_entities_to_labels(
                text_encoding=text_encoding,
                segment=segment,
                entities=entities,
                use_bilou_scheme=self.use_bilou_scheme,
            )
            tags = tag_tokens_with_labels(
                text_encoding,
                labels=labels,
                label_to_id=self.label_to_id,
                tag_all_labels=self.tag_all_labels,
            )

        model_input = {}
        model_input["input_ids"] = text_encoding.ids
        model_input["attention_masks"] = text_encoding.attention_mask
        model_input["labels"] = tags

        return model_input

    def _encode_text(self, text):
        """Return a EncodingFast instance"""
        text_tokenized = self._tokenizer(
            text,
            padding="max_length",
            max_length=self.max_length,
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
        if self._tokenizer is not None:
            self._tokenizer.save_pretrained(path)

    def load(self, path: Union[str, Path]):
        nb_labels = len(self.label_to_id)
        config = transformers.AutoConfig.from_pretrained(
            path,
            num_labels=nb_labels,
            cache_dir=self.cache_dir,
        )
        config.label2id = self.label_to_id
        config.id2label = self.id_to_label

        tokenizer = transformers.AutoTokenizer.from_pretrained(
            path, cache_dir=self.cache_dir, use_fast=True
        )

        if not isinstance(tokenizer, transformers.PreTrainedTokenizerFast):
            raise ValueError(
                "This operation only works with model that have a fast tokenizer. Check"
                " the hugging face documentation to find the required tokenizer"
            )
        model = transformers.AutoModelForTokenClassification.from_pretrained(
            path, config=config, cache_dir=self.cache_dir, ignore_mismatched_sizes=True
        )

        self._tokenizer = tokenizer
        self._model = model
