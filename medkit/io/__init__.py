__all__ = [
    "BratInputConverter",
    "BratOutputConverter",
    "RTTMInputConverter",
    "RTTMOutputConverter",
]

from medkit.core.utils import has_optional_modules

from .brat import BratInputConverter, BratOutputConverter
from .rttm import RTTMInputConverter, RTTMOutputConverter

if has_optional_modules(["spacy"]):
    # fmt: off
    from .spacy import SpacyInputConverter, SpacyOutputConverter  # noqa: F401
    __all__.append("SpacyInputConverter")
    __all__.append("SpacyOutputConverter")
    # fmt: on
