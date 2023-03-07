from __future__ import annotations
from pathlib import Path

__all__ = ["BatchData", "MetricsComputer", "check_model_for_task_HF"]

from typing import Any, Dict, List, Union
from typing_extensions import Protocol, runtime_checkable

import torch
import transformers


class BatchData(dict):
    """A BatchData pack data allowing both column and row access"""

    def __getitem__(self, index: int) -> Dict[str, Union[List[Any], torch.Tensor]]:
        if isinstance(index, str):
            inner_dict = {key: values for (key, values) in self.items()}
            return inner_dict[index]
        return {key: values[index] for key, values in self.items()}

    def to_device(self, device: torch.device) -> BatchData:
        """
        Ensure that Tensors in the BatchData object are on the specified `device`

        Parameters
        ----------
        device:
            A `torch.device` object representing the device on which tensors
            will be allocated.

        Returns
        -------
        BatchData
            A new object with the tensors on the proper device.
        """
        inner_batch = BatchData()
        for key, value in self.items():
            if isinstance(value, torch.Tensor):
                inner_batch[key] = value.to(device)
            else:
                inner_batch[key] = value
        return inner_batch


@runtime_checkable
class MetricsComputer(Protocol):
    "A MetricsComputer is the base protocol to compute metrics in training"

    def prepare_batch(
        self, model_output: BatchData, input_batch: BatchData
    ) -> Dict[str, List[Any]]:
        """Prepare a batch of data to compute the metrics

        Parameters
        ----------
        model_output: BatchData
            Output data after a model forward pass.
        input_batch: BatchData
            Preprocessed input batch

        Returns
        -------
        Dict[str, List[Any]]
            A dictionary with the required data to calculate the metric
        """
        pass

    def compute(self, all_data: Dict[str, List[Any]]) -> Dict[str, float]:
        """Compute metrics using 'all_data'

        Parameters
        ----------
        all_data: Dict[str, List[Any]]
            A dictionary to compute the metrics.
            i.e. A dictionary with a list of 'references' and a list of 'predictions'.

        Returns
        -------
        Dict[str, float]
            A dictionary with the results
        """
        pass


def check_model_for_task_HF(model: Union[str, Path], task: str) -> bool:
    """Check compatibility of a model with a task HuggingFace.
    The model could be in the HuggingFace hub or in local files.

    Parameters
    ----------
    model_name_or_path:
        Name (on the HuggingFace models hub) or path of the model.

    task:
        A string representing tha HF task to check i.e : 'token-classification'

    Returns
    -------
    bool
        Model compatibility with the task
    """
    try:
        config = transformers.AutoConfig.from_pretrained(model)
    except Exception as err:
        raise ValueError("Impossible to get the task from model. Reason : %s" % err)

    valid_config_name = [
        config_class.__name__
        for supported_classes in transformers.pipelines.SUPPORTED_TASKS[task]["pt"]
        for config_class in supported_classes._model_mapping.keys()
    ]

    return config.__class__.__name__ in valid_config_name
