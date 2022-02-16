__all__ = [
    "RegexpMatcher",
    "RegexpMatcherRule",
    "RegexpMatcherNormalization",
]

import importlib

from .regexp_matcher import RegexpMatcher, RegexpMatcherRule, RegexpMatcherNormalization

spec = importlib.util.find_spec("quickumls")
if spec is not None:
    # fmt: off
    from .quick_umls_matcher import QuickUMLSMatcher  # noqa: F401
    __all__.append("QuickUMLSMatcher")
    # fmt: on
