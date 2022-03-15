__all__ = [
    "replace_point_after_keywords",
    "replace_multiple_newline_after_sentence",
    "replace_newline_inside_sentence",
    "clean_newline_character",
    "clean_multiple_whitespaces_in_sentence",
    "clean_parentheses_eds",
    "replace_point_in_uppercase",
    "replace_point_in_numbers",
    "replace_point_before_keywords",
]


import re
from typing import List, Tuple, Union

import medkit.core.text.span as span_utils
from medkit.core.text.span import AnySpan

# Some strings for character classification
_NUMERIC_CHARS = "0-9"
_UPPERCASE_CHARS = "A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸÆŒ"
_PUNCT_CHARS = r"\.,;\?\!\:\("
_LOWERCASE_CHARS = "a-zàâäçéèêëîïôöùûüÿ"


def clean_newline_character(
    text: str, spans: List[AnySpan], keep_endlines: bool = False
) -> Tuple[str, List[AnySpan]]:
    """Replace the newline character depending on its position in the text.
    The endlines characters that are not suppressed can be either
    kept as endlines, or replaced by spaces.

    Parameters
    ----------
    text:
        The text to be modified
    spans:
        Spans associated to the `text`
    keep_endlines:
        If True, each endline is replaced by `.\\n`
        If False, each endline is replaced by `.\\s`
    Returns
    ------
        The cleaned text and the list of spans updated

    """

    text, spans = replace_newline_inside_sentence(text, spans)
    text, spans = replace_multiple_newline_after_sentence(text, spans)
    text, spans = _replace_text(
        text, spans, pattern="\n", repl=".\n" if keep_endlines else ". "
    )
    return text, spans


def clean_parentheses_eds(text: str, spans: List[AnySpan]) -> Tuple[str, List[AnySpan]]:
    """Modify the text near the parentheses depending on its content.
    The rules are adapted for French documents"""

    text, spans = _replace_text(text, spans, r"\(-\)", " negatif ", group=0)
    text, spans = _replace_text(text, spans, r"\(\+\)", " positif ", group=0)

    text, spans = _replace_big_parentheses(text, spans)
    text, spans = _replace_small_parentheses(text, spans)
    return text, spans


def clean_multiple_whitespaces_in_sentence(
    text: str, spans: List[AnySpan]
) -> Tuple[str, List[AnySpan]]:
    """Replace multiple white-spaces between alphanumeric characters and
    lowercase characters with a single whitespace"""
    alphanums_chars = _UPPERCASE_CHARS + _LOWERCASE_CHARS + _NUMERIC_CHARS
    lowernums_chars = _LOWERCASE_CHARS + _NUMERIC_CHARS

    pattern = rf"[{alphanums_chars},:](\s{{2,}})[{lowernums_chars}]"
    text, spans = _replace_text(text, spans, pattern, " ", group=1)
    return text, spans


def replace_point_after_keywords(
    text: str,
    spans: List[AnySpan],
    keywords: List[str],
    strict: bool = False,
    replace_by: str = " ",
):
    """Replace the character `.` after a keyword and update its span.
    Could be used to replace dots that indicate the title of a person (i.e. M. or Mrs.)
    or some dots that appear by mistake after `keywords`

    Parameters
    ----------
    text:
        The text to be modified
    spans:
        Spans associated to the `text`
    keywords:
        Word or pattern to match before a point
    strict:
        If True, the keyword must be followed by a point.
        If False, the keyword could have zero or many whitespaces before a point
    replace_by:
        Replacement string

    Returns
    ------
        The text with the replaced matches and the updated list of spans

    """
    # Create a list regex using '\b' to indicate that keyword is a word
    keywords_regexp = "|".join([rf"\b{keyword}" for keyword in keywords])
    if strict:
        pattern = rf"(?:{keywords_regexp})(\.)"  # point after kw
    else:
        pattern = rf"(?:{keywords_regexp})(\s*\.)"  # zero or many whitespaces after kw

    # The first group has the span of interest
    text, spans = _replace_text(text, spans, pattern, repl=replace_by, group=1)
    return text, spans


def replace_multiple_newline_after_sentence(
    text: str, spans: List[AnySpan]
) -> Tuple[str, List[AnySpan]]:
    """Replace all (non-alphanumeric) characters between a newline
    character `\\n` and a capital letter or a number with a single newline character.

    Parameters
    ----------
    text:
        The text to be modified
    spans:
        Spans associated to the `text`

    Returns
    ------
        The cleaned text and the list of spans updated

    """
    pattern = rf"(?P<blanks>\r?\n\W*)[{_NUMERIC_CHARS}{_UPPERCASE_CHARS}]"
    replace_by = "\n"
    text, spans = _replace_text(text, spans, pattern, repl=replace_by, group="blanks")
    return text, spans


def replace_newline_inside_sentence(
    text: str, spans: List[AnySpan]
) -> Tuple[str, List[AnySpan]]:
    """Replace the newline character `\\n` between lowercase letters
    or punctuation marks with a space

    Parameters
    ----------
    text:
        The text to be modified
    spans:
        Spans associated to the `text`

    Returns
    ------
        The cleaned text and the list of spans updated

    """
    pattern = rf"(?P<blanks>\r?\n[\t\r\n\t\s]*)[{_LOWERCASE_CHARS}{_PUNCT_CHARS}]"
    replace_by = " "
    text, spans = _replace_text(text, spans, pattern, repl=replace_by, group="blanks")
    return text, spans


def _replace_big_parentheses(
    text: str, spans: List[AnySpan]
) -> Tuple[str, List[AnySpan]]:
    """Modify the sentence containing large parentheses.
    The new sentence contains the text after the parentheses followed by
    the text that was inside the parentheses.
    """
    # capture multiple spaces to control the output format
    pattern = re.compile(
        r"(\s*)\((?P<txt_inside>[^)(]{30,5000})\)(\s*)(?P<txt_after>[^.]*)\."
    )

    while True:
        # iteration over the new text until no matches are found
        match = pattern.search(text)
        if match is None:
            break

        # extract groups including their spans
        txt_in, span_in = span_utils.extract(text, spans, [match.span("txt_inside")])
        txt_af, span_af = span_utils.extract(text, spans, [match.span("txt_after")])

        # insert characters before and after each group
        txt_in, span_in = span_utils.insert(txt_in, span_in, [len(txt_in)], ["."])
        txt_af, span_af = span_utils.insert(
            txt_af, span_af, [0, len(txt_af)], [" ", " ; "]
        )  # insert a space by default (eq: ' {text_af} ; ')
        # create the new phrase
        txt_new, span_new = span_utils.concatenate([txt_af, txt_in], [span_af, span_in])

        # add the new phrase into the text. Extract text_before and text_after
        # from this match and concatenate all to update texp_tmp and spans
        txt_before, span_before = span_utils.extract(text, spans, [(0, match.start(0))])
        txt_after, span_after = span_utils.extract(
            text, spans, [(match.end(0), len(text))]
        )
        text, spans = span_utils.concatenate(
            [txt_before, txt_new, txt_after], [span_before, span_new, span_after]
        )
    return text, spans


def _replace_small_parentheses(
    text: str, spans: List[AnySpan]
) -> Tuple[str, List[AnySpan]]:
    """Modify the sentence containing small parentheses.
    The new sentence has the text that was inside the parentheses surrounded by `,`
    """
    pattern = r"(\()(?:[^)(]{1,29})(\))"
    # capture each parenthesis
    group_1 = [match.span(1) for match in re.finditer(pattern, text)]
    group_2 = [match.span(2) for match in re.finditer(pattern, text)]
    ranges = sorted([*group_1, *group_2], key=lambda sp: sp[0])
    text, spans = span_utils.replace(text, spans, ranges, [","] * len(ranges))
    return text, spans


def _replace_text(
    text: str,
    spans: List[AnySpan],
    pattern: str,
    repl: str,
    group: Union[str, int] = 0,
) -> Tuple[str, List[AnySpan]]:
    """Replace matches in `text` by `repl` and update its spans."""
    ranges = [(match.span(group)) for match in re.finditer(pattern, text)]
    return span_utils.replace(text, spans, ranges, [repl] * len(ranges))


def replace_point_in_uppercase(text, spans):
    """Replace the character `.` between uppercase characters
    with a space and update its span."""
    pattern = rf"[{_UPPERCASE_CHARS}](\.)[{_UPPERCASE_CHARS}]"
    text, spans = _replace_text(text, spans, pattern, " ", group=1)
    return text, spans


def replace_point_in_numbers(text, spans):
    """Replace the character `.` between numbers
    with the character `,` a space and update its span."""
    pattern = rf"[{_NUMERIC_CHARS}](\.)[{_NUMERIC_CHARS}]"
    text, spans = _replace_text(text, spans, pattern, ",", group=1)
    return text, spans


def replace_point_before_keywords(text, spans, keywords: List[str]):
    """Replace the character `.` before a keyword
    with a space and update its span."""
    keywords_regexp = "|".join([rf"{keyword}\b" for keyword in keywords])
    pattern = rf"(\.\s*)(?:{keywords_regexp})"
    text, spans = _replace_text(text, spans, pattern, " ", group=1)
    return text, spans
