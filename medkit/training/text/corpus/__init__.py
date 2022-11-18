# datasets that returns object medkit
# we could include load methods to serialize
# or more custom datasets

__all__ = []

import importlib.util

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# Datasets
_torch_is_available = importlib.util.find_spec("torch") is not None
if _torch_is_available:
    # fmt: off
    from .AG_NEWS import AG_NEWS  # noqa: F401
    __all__.append("AG_NEWS")
    # fmt: on
