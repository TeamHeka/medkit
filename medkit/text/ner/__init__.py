__all__ = [
    "UMLSNormAttribute",
    "DucklingMatcher",
    "RegexpMatcher",
    "RegexpMatcherRule",
    "RegexpMatcherNormalization",
    "RegexpMetadata",
    "IAMSystemMatcher",
    "MedkitKeyword",
]

from medkit.core.utils import modules_are_available

from .duckling_matcher import DucklingMatcher
from .umls_norm_attribute import UMLSNormAttribute
from .regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
    RegexpMetadata,
)
from .iamsystem_matcher import IAMSystemMatcher, MedkitKeyword

# quick_umls module
if modules_are_available(["packaging", "quickumls"]):
    __all__.append("quick_umls_matcher")

# HF entity matcher
if modules_are_available(["torch", "transformers"]):
    __all__.append("hf_entity_matcher")
    __all__.append("hf_entity_matcher_trainable")

if modules_are_available(["pandas", "torch", "transformers"]):
    __all__ += ["umls_coder_normalizer"]
