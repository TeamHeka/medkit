__all__ = ["spacy_utils", "displacy_utils", "SpacyDocPipeline", "SpacyPipeline"]

# Verify that spacy is installed
from medkit.core.utils import modules_are_available

if not modules_are_available(["spacy"]):
    raise ImportError("Requires spacy install for importing medkit.text.spacy module")

from . import spacy_utils  # noqa: E402, F401
from . import displacy_utils  # noqa: E402, F401
from .doc_pipeline import SpacyDocPipeline  # noqa: E402, F401
from .pipeline import SpacyPipeline  # noqa: E402, F401
