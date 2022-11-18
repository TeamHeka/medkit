from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from typing_extensions import Protocol, runtime_checkable

import torch

from medkit.training.utils import BatchData


@runtime_checkable
class TrainableOperation(Protocol):
    """Protocol for a trainable operation"""

    @property
    def device(self) -> torch.device:
        ...

    def configure_optimizer(self, lr: float) -> torch.optim.Optimizer:
        """Create optimizer using the learning rate"""
        pass

    def preprocess(self, input: Any, inference_mode: bool) -> Dict[str, Any]:
        """
        Preprocess take the input and return a dictionnary with
        everything necessary `self.forward` to run properly.
        """
        pass

    def collate(self, batch: List[Dict[str, Any]]) -> BatchData:
        """Collate a list of samples (as returned by `preprocess`)"""
        pass

    def forward(
        self,
        input_tensors: BatchData,
        return_loss: bool,
        eval_mode: bool,
    ) -> Tuple[BatchData, Optional[torch.Tensor]]:
        """Perform the forward pass on a batch and return the corresponding
        output as well as the loss if `return_loss` is True
        """
        pass

    def postprocess(self, model_output: Dict[str, Any]) -> Any:
        """Create medkit annotations for model output"""
        pass

    def save(self, path: Union[str, Path]):
        """Save model to disk"""
        pass

    def load(self, path: Union[str, Path]):
        """Load weights from disk"""
        # model.from_pretrained or torch load
        pass
