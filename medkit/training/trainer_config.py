from __future__ import annotations

__all__ = ["TrainerConfig"]

from dataclasses import dataclass, fields
from typing import Optional, Dict, Any


@dataclass
class TrainerConfig:
    """Trainer configuration

    Parameters
    ----------
    output_dir:
        The output directory where the checkpoint will be saved.
    learning_rate:
        The initial learning rate.
    nb_training_epochs:
        Total number of training/evaluation epochs to do.
    dataloader_nb_workers:
        Number of subprocess for the data loading. The default value is 0,
        the data will be loaded in the main process. If this config is for a
        HuggingFace model, do not change this value.
    batch_size:
        Number of samples per batch to load.
    seed:
        Random seed to use with PyTorch and numpy. It should be set to ensure
        reproducibility between experiments.
    gradient_accumulation_steps:
        Number of steps to accumulate gradient before performing an optimization step.
    do_metrics_in_training:
        By default, only the custom metrics are computed using `eval_data`. If set to
        True, the custom metrics are computed also using `training_data`.
    metric_to_track_lr:
        Name of the eval metric to be tracked for updating the learning rate.
        By default, eval `loss` is tracked.
    """

    output_dir: str
    learning_rate: float = 1e-5
    nb_training_epochs: int = 3
    dataloader_nb_workers: int = 0
    batch_size: int = 1
    seed: Optional[int] = None
    gradient_accumulation_steps: int = 1
    do_metrics_in_training: bool = False
    metric_to_track_lr: str = "loss"

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            (field.name, getattr(self, field.name))
            for field in fields(self)
            if field.name != "output_dir"
        )
