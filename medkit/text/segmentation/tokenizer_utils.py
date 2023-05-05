__all__ = ["lstrip", "rstrip", "strip"]

from typing import Tuple


def lstrip(text: str, start: int = 0, chars: str = None) -> Tuple[str, int]:
    """Returns a copy of the string with leading characters removed
    and its corresponding new start index.

    Parameters
    ----------
    text
        The text to strip.
    start
        The start index from the original text if any.
    chars
        The list of characters to strip. Default behaviour is like `str.lstrip([chars])`.
    """
    new_text = text.lstrip(chars)
    new_start = start + (len(text) - len(new_text))
    return new_text, new_start


def rstrip(text: str, end: int = None, chars: str = None) -> Tuple[str, int]:
    """Returns a copy of the string with trailing characters removed
    and its corresponding new end index.

    Parameters
    ----------
    text
        The text to strip.
    end
        The end index from the original text if any.
    chars
        The list of characters to strip. Default behaviour is like `str.rstrip([chars])`.
    """
    if end is None:
        end = len(text)
    new_text = text.rstrip(chars)
    new_end = end - (len(text) - len(new_text))
    return new_text, new_end


def strip(text: str, start: int = 0, chars: str = None) -> Tuple[str, int, int]:
    """Returns a copy of the string with leading characters removed
    and its corresponding new start and end indexes.

    Parameters
    ----------
    text
        The text to strip.
    start
        The start index from the original text if any.
    chars
        The list of characters to strip. Default behaviour is like `str.lstrip([chars])`.
    """
    new_text, new_start = lstrip(text, start, chars)
    new_end = new_start + len(new_text)
    new_text, new_end = rstrip(new_text, new_end)
    return new_text, new_start, new_end
