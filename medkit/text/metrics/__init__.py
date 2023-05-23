"""
This package needs extra-dependencies not installed as core dependencies of medkit.
To install them, use `pip install medkit-lib[metrics]`.
"""
__all__ = []
from medkit.core.utils import modules_are_available

if modules_are_available(["seqeval", "transformers", "torch"]):
    __all__.append("ner")
