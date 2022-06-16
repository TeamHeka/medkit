__all__ = []
import importlib.util

spec = importlib.util.find_spec("spacy")
if spec is not None:
    # fmt: off
    from . import spacy_utils  # noqa: F401
    from .doc_pipeline import SpacyDocPipeline  # noqa: F401
    from .pipeline import SpacyPipeline  # noqa: F401
    __all__.extend(["spacy_utils", "SpacyDocPipeline", "SpacyPipeline"])
    # fmt: on
