__all__ = ["Normalizer", "NormalizerRule", "LIGATURE_RULES", "EDSCleaner"]

from .normalizer import Normalizer, NormalizerRule
from .eds_cleaner import EDSCleaner

#: Normalizer rules for ligatures (medkit.text.preprocessing.LIGATURE_RULES)
LIGATURE_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("\u00c6", "AE"),
        ("\u00E6", "ae"),
        ("\u0152", "OE"),
        ("\u0153", "oe"),
    ]
]
