__all__ = []

from medkit.core.utils import modules_are_available

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# Syntactic Relation Extractor module
if modules_are_available(["spacy"]):
    # fmt: off
    from .syntactic_relation_extractor import SyntacticRelationExtractor  # noqa: F401
    __all__.append("SyntacticRelationExtractor")
    # fmt: on
