__all__ = []
import importlib.util

spec = importlib.util.find_spec("spacy")
if spec is not None:
    # fmt: off
    from .syntactic_relation_extractor import SyntacticRelationExtractor  # noqa: F401
    __all__.append("SyntacticRelationExtractor")
    # fmt: on
