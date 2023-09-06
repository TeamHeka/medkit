__all__ = [
    "ALL_CHAR_RULES",
    "LIGATURE_RULES",
    "FRACTION_RULES",
    "SIGN_RULES",
    "SPACE_RULES",
    "DOT_RULES",
    "QUOTATION_RULES",
]

#: Rules for ligatures
LIGATURE_RULES = [
    ("\u00c6", "AE"),
    ("\u00E6", "ae"),
    ("\u0152", "OE"),
    ("\u0153", "oe"),
]
#: Rules for fraction characters
FRACTION_RULES = [
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
#: Rules for non-standard spaces
SPACE_RULES = [
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
]

#: Rules for sign chars
SIGN_RULES = [
    ("\u00A9", ""),  # copyright
    ("\u00AE", ""),  # registered
    ("\u2122", ""),  # trade
]

#: Rules for dot chars
DOT_RULES = [
    # horizontal ellipsis
    ("\u2026", "..."),
    ("\u22EF", "..."),
]

#: RegexpReplacer quotation marks: replace double and single quotation marks
QUOTATION_RULES = [
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

#: All pre-defined rules for CharReplacer
ALL_CHAR_RULES = (
    DOT_RULES
    + FRACTION_RULES
    + LIGATURE_RULES
    + QUOTATION_RULES
    + SIGN_RULES
    + SPACE_RULES
)
