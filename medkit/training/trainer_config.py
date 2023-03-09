from __future__ import annotations

__all__ = ["TrainerConfig"]

from dataclasses import dataclass, fields
from typing import Optional, Dict, Any


@dataclass
class TrainerConfig:
    """Trainer configuration"""

    output_dir: str
    learning_rate: float = 1e-5
    nb_training_epochs: int = 3
    dataloader_nb_workers: int = 0
    batch_size: int = 1
    seed: Optional[int] = None
    gradient_accumulation_steps: int = 1
    do_metrics_in_training: bool = False
    metric_to_track_lr: str = "loss"
    log_step_interval: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            (field.name, getattr(self, field.name))
            for field in fields(self)
            if field.name != "output_dir"
        )
