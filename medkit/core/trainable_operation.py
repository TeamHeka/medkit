from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from typing_extensions import Protocol, runtime_checkable

import torch

from medkit.training.utils import BatchData


@runtime_checkable
class TrainableOperation(Protocol):
    """A TrainableOperation is the base protocol for an operation to be trainable"""

    @property
    def device(self) -> torch.device:
        pass

    def configure_optimizer(self, lr: float) -> torch.optim.Optimizer:
        """Create optimizer using the learning rate"""
        pass

    def preprocess(self, input: Any, inference_mode: bool) -> Dict[str, Any]:
        """
        Preprocess the input and return a dictionary with
        everything needed for the forward pass.

        This method is intended to preprocess an input, `self.collate` must be
        used to generate batches for `self.forward` to run properly.

        `inference_mode` indicates the phase of the call. If `inference_mode` is False,
        the call is made in a training context, so preprocess must generate labels to
        compute a loss. If `inference_mode` is True, the call is made in an inference context,
        the input has no label to preprocess.
        """
        pass

    def collate(self, batch: List[Dict[str, Any]]) -> BatchData:
        """Collate a list of data processed by `preprocess` to form a batch"""
        pass

    def forward(
        self,
        input_batch: BatchData,
        return_loss: bool,
        eval_mode: bool,
    ) -> Tuple[BatchData, Optional[torch.Tensor]]:
        """Perform the forward pass on a batch and return the corresponding
        output as well as the loss if `return_loss` is True.

        Before forwarding the model, this method must set the model to training
        or evaluation mode depending on `eval_mode`. In PyTorch models there are
        two methods to set the mode `model.train()` and `model.eval()`
        """
        pass

    def postprocess(self, model_output: BatchData) -> Any:
        """Create a medkit annotation for model output"""
        pass

    def save(self, path: Union[str, Path]):
        """Save model to disk"""
        pass

    def load(self, path: Union[str, Path]):
        """Load weights from disk"""
        # model.from_pretrained or torch load
        pass
