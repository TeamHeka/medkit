__all__ = []

import importlib.util

_torch_is_available = importlib.util.find_spec("torch") is not None
_transformers_is_available = importlib.util.find_spec("transformers") is not None
if _transformers_is_available and _torch_is_available:
    # fmt: off
    from .hf_translator import HFTranslator  # noqa: F401
    __all__.append("HFTranslator")
    # fmt: on
