__all__ = ["Normalizer", "NormalizerRule", "LIGATURE_RULES"]

from .normalizer import Normalizer, NormalizerRule


LIGATURE_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("\u00c6", "AE"),
        ("\u00E6", "ae"),
        ("\u0152", "OE"),
        ("\u0153", "oe"),
    ]
]
