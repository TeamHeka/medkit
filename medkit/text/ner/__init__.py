__all__ = [
    "UMLSNormalization",
    "DucklingMatcher",
    "RegexpMatcher",
    "RegexpMatcherRule",
    "RegexpMatcherNormalization",
    "RegexpMetadata",
]

import importlib.util

from .duckling_matcher import DucklingMatcher
from .umls_normalization import UMLSNormalization
from .regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
    RegexpMetadata,
)

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# quick_umls module
_packaging_is_available = importlib.util.find_spec("packaging") is not None
_quickumls_is_available = importlib.util.find_spec("quickumls") is not None
if _packaging_is_available and _quickumls_is_available:
    # fmt: off
    from .quick_umls_matcher import QuickUMLSMatcher  # noqa: F401
    __all__.append("QuickUMLSMatcher")
    # fmt: on

# HF entity matcher
_torch_is_available = importlib.util.find_spec("torch") is not None
_transformers_is_available = importlib.util.find_spec("transformers") is not None
if _torch_is_available and _transformers_is_available:
    # fmt: off
    from .hf_entity_matcher import HFEntityMatcher  # noqa: F401
    __all__.append("HFEntityMatcher")
    # fmt: on

_pandas_is_available = importlib.util.find_spec("pandas") is not None
_torch_is_available = importlib.util.find_spec("torch") is not None
_transformers_is_available = importlib.util.find_spec("transformers") is not None
if _pandas_is_available and _torch_is_available and _transformers_is_available:
    # fmt: off
    from .umls_coder_normalizer import UMLSCoderNormalizer  # noqa: F401
    __all__ += ["UMLSCoderNormalizer"]
    # fmt: on
