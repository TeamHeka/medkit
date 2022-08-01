__all__ = ["context", "ner", "segmentation", "relations", "translation"]

import importlib.util
from . import context
from . import ner
from . import segmentation
from . import relations
from . import translation

_spacy_is_available = importlib.util.find_spec("spacy") is not None
if _spacy_is_available:
    # fmt: off
    from . import spacy  # noqa: F401
    __all__.append("spacy")
    # fmt: on
