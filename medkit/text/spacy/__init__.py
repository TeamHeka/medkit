__all__ = ["spacy_utils", "displacy_utils", "SpacyDocPipeline", "SpacyPipeline"]

# Verify that spacy is installed
import importlib.util

_spacy_is_available = importlib.util.find_spec("spacy") is not None
if not _spacy_is_available:
    raise ImportError("Requires spacy install for importing medkit.text.spacy module")

from . import spacy_utils  # noqa: E402, F401
from . import displacy_utils  # noqa: E402, F401
from .doc_pipeline import SpacyDocPipeline  # noqa: E402, F401
from .pipeline import SpacyPipeline  # noqa: E402, F401
