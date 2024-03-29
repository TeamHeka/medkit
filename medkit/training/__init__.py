"""
This package needs extra-dependencies not installed as core dependencies of medkit.
To install them, use `pip install medkit-lib[training]`.
"""

__all__ = [
    "TrainerCallback",
    "DefaultPrinterCallback",
    "Trainer",
    "TrainerConfig",
    "BatchData",
    "MetricsComputer",
    "TrainableComponent",
]

# Verify that torch is installed
from medkit.core.utils import modules_are_available

if not modules_are_available(["torch"]):
    raise ImportError("Requires torch install for importing medkit.training module")

from .callbacks import TrainerCallback, DefaultPrinterCallback
from .trainer import Trainer
from .trainer_config import TrainerConfig
from .utils import BatchData, MetricsComputer
from .trainable_component import TrainableComponent
