__all__ = [
    "DucklingMatcher",
    "RegexpMatcher",
    "RegexpMatcherRule",
    "RegexpMatcherNormalization",
    "RegexpMetadata",
]

import importlib.util

from .duckling_matcher import DucklingMatcher
from .regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
    RegexpMetadata,
)

_packaging_is_available = importlib.util.find_spec("packaging") is not None
_quickumls_is_available = importlib.util.find_spec("quickumls") is not None
_six_is_available = importlib.util.find_spec("six") is not None
if _packaging_is_available and _quickumls_is_available and _six_is_available:
    # fmt: off
    from .quick_umls_matcher import QuickUMLSMatcher  # noqa: F401
    __all__.append("QuickUMLSMatcher")
    # fmt: on
