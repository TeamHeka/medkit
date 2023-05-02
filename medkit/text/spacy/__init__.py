"""
This package needs extra-dependencies not installed as core dependencies of medkit.
To install them, use `pip install medkit-lib[spacy]`.
"""

__all__ = [
    "SpacyDocPipeline",
    "SpacyPipeline",
    # not imported
    "spacy_utils",
    "displacy_utils",
]

# Verify that spacy is installed
from medkit.core.utils import modules_are_available

if not modules_are_available(["spacy"]):
    raise ImportError("Requires spacy install for importing medkit.text.spacy module")

from .doc_pipeline import SpacyDocPipeline  # noqa: E402, F401
from .pipeline import SpacyPipeline  # noqa: E402, F401

if modules_are_available(["edsnlp"]):
    __all__.append("edsnlp")
