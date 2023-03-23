__all__ = [
    "BratInputConverter",
    "BratOutputConverter",
    "medkit_json",
    "RTTMInputConverter",
    "RTTMOutputConverter",
]

from medkit.core.utils import modules_are_available

from .brat import BratInputConverter, BratOutputConverter
from . import medkit_json
from .rttm import RTTMInputConverter, RTTMOutputConverter

if modules_are_available(["spacy"]):
    # fmt: off
    from .spacy import SpacyInputConverter, SpacyOutputConverter  # noqa: F401
    __all__.append("SpacyInputConverter")
    __all__.append("SpacyOutputConverter")
    # fmt: on
