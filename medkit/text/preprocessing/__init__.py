__all__ = [
    "Normalizer",
    "NormalizerRule",
    "LIGATURE_RULES",
    "FRACTION_RULES",
    "SIGN_RULES",
    "SPACE_RULES",
    "EDSCleaner",
]

from .normalizer import Normalizer, NormalizerRule
from .eds_cleaner import EDSCleaner

#: Normalizer rules for ligatures
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
        ("\u2189", "0/3"),
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

#: Normalizer rules for sign chars
SIGN_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("\u00A9", ""),  # copyright
        ("\u00AE", ""),  # registered
        ("\u2122", ""),  # trade
    ]
]

#: Normalizer rules for dot chars
DOT_RULES = [
    NormalizerRule(*rule)
    for rule in [("\u2026", "..."), ("\u22EF", "...")]  # horizontal ellipsis
]

#: Normalizer quotation marks
# replace double and single quotation marks
QUOTATION_RULES = [
    NormalizerRule(*rule)
    for rule in [
        ("»", '"'),  # normalize double quotation marks
        ("«", '"'),  # replace double quotation marks
        ("\u201C", '"'),
        ("\u201D", '"'),
        ("\u201E", '"'),
        ("\u201F", '"'),
        ("\u2039", '"'),
        ("\u203A", '"'),
        ("\u02F5", '"'),
        ("\u02F6", '"'),
        ("\u02DD", '"'),
        ("\uFF02", '"'),
        ("\u201A", ""),  # single low quotation (remove)
        ("\u2018", "'"),  # left side single quotation
        ("\u2019", "'"),  # right side single quotation
        ("\u201B", "'"),  # single high reverse quotation
        ("\u02CA", "'"),  # grave accent
        ("\u0060", "'"),
        ("\u02CB", "'"),  # acute accent
        ("\u00B4", "'"),
    ]
]
