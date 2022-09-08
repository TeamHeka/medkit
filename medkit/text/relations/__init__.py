__all__ = []
import importlib.util

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# Syntactic Relation Extractor module
_spacy_is_available = importlib.util.find_spec("spacy") is not None
if _spacy_is_available:
    # fmt: off
    from .syntactic_relation_extractor import SyntacticRelationExtractor  # noqa: F401
    __all__.append("SyntacticRelationExtractor")
    # fmt: on
