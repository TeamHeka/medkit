__all__ = []

from medkit.core.utils import has_optional_modules

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# Syntactic Relation Extractor module
if has_optional_modules(["spacy"]):
    # fmt: off
    from .syntactic_relation_extractor import SyntacticRelationExtractor  # noqa: F401
    __all__.append("SyntacticRelationExtractor")
    # fmt: on
