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
#: Normalizer rules for fraction characters
FRACTION_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("\u00BC", "1/4"),
        ("\u00BD", "1/2"),
        ("\u00BE", "3/4"),
        ("\u2150", "1/7"),
        ("\u2151", "1/9"),
        ("\u2152", "1/10"),
        ("\u2153", "1/3"),
        ("\u2154", "2/3"),
        ("\u2155", "1/5"),
        ("\u2156", "2/5"),
        ("\u2157", "3/5"),
        ("\u2158", "4/5"),
        ("\u2159", "1/6"),
        ("\u215A", "5/6"),
        ("\u215B", "1/8"),
        ("\u215C", "3/8"),
        ("\u215D", "5/8"),
        ("\u215E", "7/8"),
        ("\u2189", "0"),
    ]
]
#: Normalizer rules for non-standard spaces
SPACE_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("\u00A0", " "),
        ("\u1680", " "),
        ("\u2002", " "),
        ("\u2003", " "),
        ("\u2004", " "),
        ("\u2005", " "),
        ("\u2006", " "),
        ("\u2007", " "),
        ("\u2008", " "),
        ("\u2009", " "),
        ("\u200A", " "),
        ("\u200B", " "),
        ("\u202F", " "),
        ("\u205F", " "),
        ("\u2420", " "),
        ("\u3000", " "),
        ("\u303F", " "),
        ("\uFEFF", " "),
        ("\u1DA7F", " "),
        ("\u1DA80", " "),
        ("\uE0020", " "),
    ]
]

#: Normalizer special chars
SPECIAL_CHARS_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("\u00A9", ""),  # copyright
        ("\u00AE", ""),  # registered
        ("\u2122", ""),  # trade
        ("°C", "Celsius"),
        ("°F", "Fahrenheit"),
        ("°", " "),  # replace degree symbol
        ("\u2026", ""),  # horizontal ellipsis
    ]
]

#: Normalizer quotation marks
# remove double quotation marks
# replace single quotation marks
QUOTATION_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("»", ""),  # remove double quotation marks
        ("«", ""),  # remove double quotation marks
        ("\u0022", ""),
        ("\u201C", ""),
        ("\u201D", ""),
        ("\u201E", ""),
        ("\u201F", ""),
        ("\u2039", ""),
        ("\u203A", ""),
        ("\u201A", ""),  # single low quotation (remove)
        ("\u2018", "'"),  # left side single quotation
        ("\u2019", "'"),  # right side single quotation
        ("\u201B", "'"),  # single high reverse quotation
        ("`", "'"),  # grave accent
    ]
]
