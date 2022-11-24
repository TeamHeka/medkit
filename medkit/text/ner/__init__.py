__all__ = [
    "UMLSNormalization",
    "DucklingMatcher",
    "RegexpMatcher",
    "RegexpMatcherRule",
    "RegexpMatcherNormalization",
    "RegexpMetadata",
]

from medkit.core.utils import has_optional_modules

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
if has_optional_modules(["packaging", "quickumls"]):
    # fmt: off
    from .quick_umls_matcher import QuickUMLSMatcher  # noqa: F401
    __all__.append("QuickUMLSMatcher")
    # fmt: on

# HF entity matcher
if has_optional_modules(["torch", "transformers"]):
    # fmt: off
    from .hf_entity_matcher import HFEntityMatcher  # noqa: F401
    __all__.append("HFEntityMatcher")
    # fmt: on

if has_optional_modules(["pandas", "torch", "transformers"]):
    # fmt: off
    from .umls_coder_normalizer import UMLSCoderNormalizer  # noqa: F401
    __all__ += ["UMLSCoderNormalizer"]
    # fmt: on
