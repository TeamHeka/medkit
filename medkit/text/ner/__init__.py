__all__ = [
    "ADICAPNormAttribute",
    "UMLSNormAttribute",
    "DucklingMatcher",
    "RegexpMatcher",
    "RegexpMatcherRule",
    "RegexpMatcherNormalization",
    "RegexpMetadata",
    "IAMSystemMatcher",
    "MedkitKeyword",
    "DateAttribute",
    "DurationAttribute",
    "RelativeDateAttribute",
    "RelativeDateDirection",
]

from medkit.core.utils import modules_are_available

from .adicap_norm_attribute import ADICAPNormAttribute
from .duckling_matcher import DucklingMatcher
from .umls_norm_attribute import UMLSNormAttribute
from .regexp_matcher import (
    RegexpMatcher,
    RegexpMatcherRule,
    RegexpMatcherNormalization,
    RegexpMetadata,
)
from .iamsystem_matcher import IAMSystemMatcher, MedkitKeyword
from .date_attribute import (
    DateAttribute,
    DurationAttribute,
    RelativeDateAttribute,
    RelativeDateDirection,
)

# quick_umls module
if modules_are_available(["packaging", "quickumls"]):
    __all__.append("quick_umls_matcher")

# HF entity matcher
if modules_are_available(["torch", "transformers"]):
    __all__.append("hf_entity_matcher")
    __all__.append("hf_entity_matcher_trainable")

if modules_are_available(["pandas", "torch", "transformers"]):
    __all__ += ["umls_coder_normalizer"]

if modules_are_available(["edsnlp"]):
    __all__ += ["tnm_attribute"]
