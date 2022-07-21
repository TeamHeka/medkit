__all__ = ["BratInputConverter", "BratOutputConverter"]

import importlib.util
from .brat import BratInputConverter, BratOutputConverter

_spacy_is_available = importlib.util.find_spec("spacy") is not None
if _spacy_is_available:
    # fmt: off
    from .spacy import SpacyInputConverter, SpacyOutputConverter  # noqa: F401
    __all__.append("SpacyInputConverter")
    __all__.append("SpacyOutputConverter")
    # fmt: on
