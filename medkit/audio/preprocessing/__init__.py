__all__ = []

import importlib.util

_resampy_is_available = importlib.util.find_spec("resampy") is not None
if _resampy_is_available is not None:
    # fmt: off
    from .resampler import Resampler  # noqa: F401
    __all__.append("Resampler")
    # fmt: on
