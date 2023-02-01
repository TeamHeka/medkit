import os
from pathlib import Path
from typing import List, Any, Dict, Iterable, Optional, Union, Tuple

import torch
import logging

from medkit.core.annotation import Attribute
from medkit.core.text.annotation import Segment

# We could imagine that TrainableOperation is like a Pipeline in transformers
# with train methods. They have a model, tokenizer, and preprocess,post models

# We should create HFTrainableOperation that supports automodel from the hub


from medkit.training.text.models.textcat import TextCat, TextCatConfig, TextCatTokenizer
from medkit.training.utils import BatchData

PYTORCH_MODEL_NAME = "pytorch_model.bin"
logger = logging.getLogger(__name__)


class PyTextClassificator:
    def __init__(
        self,
        model_path: Optional[str] = None,
        output_label: str = "category",
        device="cpu",
    ):
        # pretrained tokenizer
        self.tokenizer = TextCatTokenizer()
        # load architecture
        # this operation only support the 'TextCat' architecture
        model_config = TextCatConfig(vocab_size=self.tokenizer.vocab_size)
        self.model = TextCat(model_config)
        if model_path is None:
            logger.warning("Loading model from scratch")
        else:
            self.load(model_path)
        self.device = torch.device(device)
        self.to(self.device)

        self.id2label = {1: "World", 2: "Sports", 3: "Business", 4: "Sci/Tec"}
        self.label2id = {"World": 1, "Sports": 2, "Business": 3, "Sci/Tec": 4}
        self.output_label = output_label  # attribute name

    def preprocess(
        self,
        input: Segment,
        inference_mode: bool = False,
    ) -> Dict[str, Any]:
        model_inputs = {}

        model_inputs["inputs_ids"] = torch.tensor(
            self.tokenizer.get_input_ids(input.text), dtype=torch.int64
        )
        attribute = input.get_attrs_by_label(self.output_label)
        if not inference_mode:
            if not attribute:
                raise ValueError(
                    f"Attr '{self.output_label}' was not found in the corpus"
                )
            value = self.label2id[attribute[0].value] - 1
            model_inputs["labels"] = torch.tensor(value, dtype=torch.int64)
        model_inputs["offsets"] = torch.tensor([0])
        return model_inputs

    def forward(
        self,
        model_inputs: BatchData,
        return_loss: bool,
        eval_mode: bool,
    ) -> Tuple[BatchData, Optional[torch.Tensor]]:
        if eval_mode:
            self.model.eval()
        else:
            self.model.train()

        logits = self.model.forward(model_inputs["inputs_ids"], model_inputs["offsets"])
        if return_loss:
            if "labels" not in model_inputs or len(model_inputs["labels"]) == 0:
                raise ValueError("Labels not in 'model_inputs', can not compute loss")
            loss = self.model.compute_loss(logits, model_inputs["labels"])
        else:
            loss = None
        return BatchData(logits=logits), loss

    def postprocess(self, model_output: Dict[str, Any]) -> Attribute:
        output = model_output["logits"].cpu().detach()
        value = output.argmax().item() + 1
        attribute = Attribute(label=self.output_label, value=str(self.id2label[value]))
        return attribute

    def collate(self, batch: List[Dict[str, Any]]) -> BatchData:
        """Function to collate a batch of model inputs"""
        labels, inputs_ids, offsets = [], [], [0]

        for sample in batch:
            inputs_ids.append(sample["inputs_ids"])
            offsets.append(sample["inputs_ids"].size(0))
            if "labels" in sample:
                labels.append(sample["labels"])

        labels = torch.tensor(labels, dtype=torch.int64)
        offsets = torch.tensor(offsets[:-1]).cumsum(dim=0)
        inputs_ids = torch.cat(inputs_ids)
        return BatchData(
            {"inputs_ids": inputs_ids, "offsets": offsets, "labels": labels}
        )

    def configure_optimizer(self, lr: float) -> torch.optim.Optimizer:
        parameters = self.model.parameters()
        optimizer = torch.optim.SGD(parameters, lr=lr)
        return optimizer

    def to(self, device: torch.device):
        self.model.to(device)

    def run(self, inputs: Iterable[Segment]):
        for segment in inputs:
            # todo:create a mini batch
            model_inputs = self.collate([self.preprocess(segment, inference_mode=True)])
            model_inputs = model_inputs.to_device(self.device)
            with torch.no_grad():
                model_output = self.forward(
                    model_inputs, eval_mode=True, return_loss=False
                )
            output = self.postprocess(model_output[0])
            print(output)

    def save(self, path: Path):
        output_path = os.path.join(path, PYTORCH_MODEL_NAME)
        torch.save(self.model.state_dict(), output_path)

    def load(self, path: Union[str, Path]):
        if isinstance(path, str):
            path = Path(path)

        model_path = os.path.join(path, PYTORCH_MODEL_NAME)
        if not os.path.isfile(model_path):
            raise ValueError(f"Can't find a valid model at '{path}'")

        state_dict = torch.load(model_path)
        self.model.load_state_dict(state_dict)
        logger.warning(f"The model was loaded correctly from '{path}'")
