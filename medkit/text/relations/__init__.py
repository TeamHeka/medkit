__all__ = []
import importlib.util

_spacy_is_available = importlib.util.find_spec("spacy") is not None
if _spacy_is_available:
    # fmt: off
    from .syntactic_relation_extractor import SyntacticRelationExtractor  # noqa: F401
    __all__.append("SyntacticRelationExtractor")
    # fmt: on
