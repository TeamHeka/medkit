__all__ = [
    "TrainerCallback",
    "DefaultPrinterCallback",
    "Trainer",
    "TrainerConfig",
    "BatchData",
    "MetricsComputer",
]

# Verify that torch is installed
from medkit.core.utils import modules_are_available

if not modules_are_available(["torch"]):
    raise ImportError("Requires torch install for importing medkit.training module")

from .callbacks import TrainerCallback, DefaultPrinterCallback
from .trainer import Trainer, TrainerConfig
from .utils import BatchData, MetricsComputer


if modules_are_available(["transformers"]):
    # fmt: off
    from .utils import check_model_for_task_HF  # noqa: F401
    __all__ += ["check_model_for_task_HF"]
    # fmt: on
