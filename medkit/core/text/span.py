__all__ = [
    "Span",
    "AdditionalSpan",
    "replace",
    "remove",
    "extract",
    "insert",
    "move",
    "normalize_spans",
]

import dataclasses
from typing import List, NamedTuple, Tuple, Union


class Span(NamedTuple):
    """
    Slice of text extracted from the original text

    Attributes
    ----------
    start: int
        Index of the first character in the original text
    end: int
        Index of the last character in the original text, plus one
    """

    start: int
    end: int

    @property
    def length(self):
        return self.end - self.start


@dataclasses.dataclass
class AdditionalSpan:
    """
    Slice of text not present in the original text

    Attributes
    ----------
    length:
        Number of characters
    replaced_spans:
        Slices of the original text that this span is replacing
    """

    length: int
    replaced_spans: List[Span]


def replace(
    text: str,
    spans: List[Union[Span, AdditionalSpan]],
    ranges: List[Tuple[int, int]],
    replacement_texts: List[str],
) -> Tuple[str, List[Union[Span, AdditionalSpan]]]:
    """Replace parts of a text, and update accordingly its associated spans

    Parameters
    ----------
    text:
        The text in which some parts will be replaced
    spans:
        The spans associated with `text`
    ranges:
        The ranges of the parts that will be replaced (end excluded),
        sorted by ascending order
    replacements_texts:
        The strings to use as replacements
        (must be the same length as `ranges`)

    Returns
    -------
    text:
        The updated text
    spans:
        The spans associated with the updated text

    Example
    -------
    >>> text = "Hello, my name is John Doe."
    >>> spans = [Span(0, len(text))]
    >>> ranges = [(0, 5), (18, 22)]
    >>> replacements = ["Hi", "Jane"]
    >>> text, spans = replace(text, spans, ranges, replacements)
    >>> print(text)
    Hi, my name is Jane Doe.
    """
    assert len(ranges) == len(replacement_texts)
    if len(ranges) == 0:
        return text, spans

    offset = 0
    replacement_lengths = []
    for (range_start, range_end), rep_text in zip(ranges, replacement_texts):
        range_start += offset
        range_end += offset
        text = text[:range_start] + rep_text + text[range_end:]

        rep_length = len(rep_text)
        offset += rep_length - (range_end - range_start)
        replacement_lengths.append(rep_length)

    spans = _replace_in_spans(spans, ranges, replacement_lengths)
    return text, spans


def _replace_in_spans(spans, ranges, replacement_lengths):
    output_spans = []

    # current span and associated values
    span_index = 0
    span = spans[0]
    # start and end in "relative" coords (can be compared to range start/end)
    span_start = 0
    span_end = span.length

    # current range to replace and associated values
    range_index = 0
    range_start, range_end = ranges[0]
    replacement_length = replacement_lengths[0]
    replaced_spans = [] if replacement_length > 0 else None

    while span_index < len(spans) or range_index < len(ranges):
        # iterate to next range if current range has been fully handled
        if range_index < len(ranges) and range_end <= span_start:
            # we have encountered all spans overlaping with the range to replace,
            # and we have stored the overlaping parts in replaced_spans.
            # create new AdditionalSpan referrencing all the replaced_spans
            # and add it to output
            # (expect if replacement_length is 0, in which case the spans were
            # just removed)
            if replacement_length > 0:
                new_span = AdditionalSpan(replacement_length, replaced_spans)
                output_spans.append(new_span)

            # move on to next span if we haven't reached end of ranges
            # and updated associated values
            range_index += 1
            if range_index < len(ranges):
                range_start, range_end = ranges[range_index]
                replacement_length = replacement_lengths[range_index]
                replaced_spans = [] if replacement_length > 0 else None

        # iterate to next span if current span has been fully handled
        if (
            span_end == span_start
            or range_index == len(ranges)
            or span_end <= range_start
        ):
            # add current span to output
            if span_end != span_start:
                output_spans.append(span)
            # move on to next span if we haven't reached end of spans
            # and updated associated values
            span_index += 1
            span_start = span_end  # end of previous span is start of new span
            if span_index < len(spans):
                span = spans[span_index]
                span_end = span_start + span.length
            continue

        # compute parts of span that do not overlap with current range
        length_before_range = max(range_start - span_start, 0)
        length_after_range = max(span_end - range_end, 0)

        # store part of span that will be replaced
        if (
            replacement_length > 0
            and length_before_range + length_after_range < span.length
        ):
            if isinstance(span, Span):
                replaced_span = Span(
                    start=span.start + length_before_range,
                    end=span.end - length_after_range,
                )
                replaced_spans.append(replaced_span)
            else:
                # keep reference to all the replaced_spans in original AdditionalSpan
                # (not possible to know which subpart of the replaced_spans corresponds
                # to the overlap between the AdditionalSpan and the range)
                assert isinstance(span, AdditionalSpan)
                replaced_spans += span.replaced_spans

        # create span for the part before the range
        # and add it to output
        if length_before_range > 0:
            if isinstance(span, Span):
                before_span = Span(
                    start=span.start, end=span.start + length_before_range
                )
            else:
                # create new AdditionalSpan covering only the length before the range,
                # but referencing the same replaced_spans
                # (not possible to know which subpart of the replaced_spans corresponds
                # to the part of the AdditionalSpan before the range)
                assert isinstance(span, AdditionalSpan)
                before_span = AdditionalSpan(
                    length=length_before_range, replaced_spans=span.replaced_spans
                )
            output_spans.append(before_span)

        # create span for the remaining part after the range
        # and use it as current span
        if length_after_range > 0:
            if isinstance(span, Span):
                span = Span(start=span.end - length_after_range, end=span.end)
            else:
                # create new AdditionalSpan covering only the length after the range,
                # but referencing the same replaced_spans
                # (not possible to know which subpart of the replaced_spans corresponds
                # to the part of the AdditionalSpan after the range)
                assert isinstance(span, AdditionalSpan)
                span = AdditionalSpan(
                    length=length_after_range, replaced_spans=span.replaced_spans
                )
        # update span_start to point to the begining of the remainder
        span_start = span_end - length_after_range

    return output_spans


def remove(
    text: str,
    spans: List[Union[Span, AdditionalSpan]],
    ranges: List[Tuple[int, int]],
) -> Tuple[str, List[Union[Span, AdditionalSpan]]]:
    """Remove parts of a text, while also removing accordingly its associated spans

    Parameters
    ----------
    text:
        The text in which some parts will be removed
    spans:
        The spans associated with `text`
    ranges:
        The ranges of the parts that will be removed (end excluded),
        sorted by ascending order

    Returns
    -------
    text:
        The updated text
    spans:
        The spans associated with the updated text
    """
    if len(ranges) == 0:
        return text, spans

    offset = 0
    for range_start, range_end in ranges:
        range_start += offset
        range_end += offset
        text = text[:range_start] + text[range_end:]
        offset -= range_end - range_start

    spans = _remove_in_spans(spans, ranges)
    return text, spans


def _remove_in_spans(spans, ranges):
    replacement_lengths = [0] * len(ranges)
    return _replace_in_spans(spans, ranges, replacement_lengths)


def extract(
    text: str,
    spans: List[Union[Span, AdditionalSpan]],
    ranges: List[Tuple[int, int]],
) -> Tuple[str, List[Union[Span, AdditionalSpan]]]:
    """Extract parts of a text as well as its associated spans

    Parameters
    ----------
    text:
        The text to extract parts from
    spans:
        The spans associated with `text`
    ranges:
        The ranges of the parts to extract (end excluded),
        sorted by ascending order

    Returns
    -------
    text:
        The extracted text
    spans:
        The spans associated with the extracted text
    """
    if len(ranges) == 0:
        return "", []

    text = "".join(text[s:e] for s, e in ranges)
    spans = _extract_in_spans(spans, ranges)
    return text, spans


def _extract_in_spans(spans, ranges):
    ranges_to_remove = []

    first_range_start = ranges[0][0]
    ranges_to_remove.append((0, first_range_start))

    ranges_to_remove += [
        (end_1, start_2) for (_, end_1), (start_2, _) in zip(ranges, ranges[1:])
    ]

    last_range_end = ranges[-1][1]
    total_length = sum(s.length for s in spans)
    ranges_to_remove.append((last_range_end, total_length))

    return _remove_in_spans(spans, ranges_to_remove)


def insert(
    text: str,
    spans: List[Union[Span, AdditionalSpan]],
    positions: List[int],
    insertion_texts: List[str],
) -> Tuple[str, List[Union[Span, AdditionalSpan]]]:
    """Insert strings in text, and update accordingly its associated spans

    Parameters
    ----------
    text:
        The text in which some strings will be inserted
    spans:
        The spans associated with `text`
    positions:
        The positions where the strings will be inserted,
        sorted by ascending order
    insertion_texts:
        The strings to insert (must be the same length as `positions`)

    Returns
    -------
    text:
        The updated text
    spans:
        The spans associated with the updated text

    Example
    -------
    >>> text = "Hello, my name is John Doe."
    >>> spans = [Span(0, len(text))]
    >>> positions = [5]
    >>> inserts = [" everybody"]
    >>> text, spans = insert(text, spans, positions, inserts)
    >>> print(text)
    Hello everybody, my name is John Doe."
    """

    assert len(positions) == len(insertion_texts)
    if len(positions) == 0:
        return text, spans

    offset = 0
    insertion_lengths = []
    for position, insertion_text in zip(positions, insertion_texts):
        position += offset
        text = text[:position] + insertion_text + text[position:]

        insertion_length = len(insertion_text)
        offset += insertion_length
        insertion_lengths.append(insertion_length)

    spans = _insert_in_spans(spans, positions, insertion_lengths)
    return text, spans


def _insert_in_spans(spans, positions, insertion_lengths):
    ranges = [(p, p) for p in positions]
    return _replace_in_spans(spans, ranges, insertion_lengths)


def move(
    text: str,
    spans: List[Union[Span, AdditionalSpan]],
    range: Tuple[int, int],
    destination: int,
) -> Tuple[str, List[Union[Span, AdditionalSpan]]]:
    """Move part of a text to another position, also moving its associated spans

    Parameters
    ----------
    text:
        The text in which a part should be moved
    range:
        The range of the part to move (end excluded)
    destination:
        The position where to insert the displaced range

    Returns
    -------
    text:
        The updated text
    spans:
        The spans associated with the updated text

    Example
    -------
    >>> text = "Hello, my name is John Doe."
    >>> spans = [Span(0, len(text))]
    >>> range = (17, 22)
    >>> dest = len(text) - 1
    >>> text, spans = move(text, spans, range, dest)
    >>> print(text)
    Hi, my name is Doe John.
    """
    spans = _move_in_spans(spans, range, destination)

    start, end = range
    text_to_move = text[start:end]
    text = text[:start] + text[end:]
    if destination > end:
        length = end - start
        destination -= length
    text = text[:destination] + text_to_move + text[destination:]

    return text, spans


def _move_in_spans(spans, range, destination):
    start, end = range
    length = end - start
    assert not (start < destination <= end)
    spans_to_move = _extract_in_spans(spans, [(start, end)])

    spans = _remove_in_spans(spans, [(start, end)])
    if destination > end:
        destination -= length

    if destination > 0:
        spans_before = _extract_in_spans(spans, [(0, destination)])
    else:
        spans_before = []
    total_length = sum(s.length for s in spans)
    if destination < total_length:
        spans_after = _extract_in_spans(spans, [(destination, total_length)])
    else:
        spans_after = []

    spans = spans_before + spans_to_move + spans_after
    return spans


def normalize_spans(spans: List[Union[Span, AdditionalSpan]]) -> List[Span]:
    """
    Return a transformed of `spans` in which all instances of AdditionalSpan are
    replaced by the spans they refer to, and in which contiguous spans are merged.

    Parameters
    ----------
    spans:
        The spans associated with a text, including additional spans if
        insertions or replacement were performed

    Returns
    -------
    normalized_spans:
        Spans in `spans` normalized as described

    Example
    ------
    >>> spans = [Span(0, 10), Span(20, 30), AdditionalSpan(8, replaced_spans=[Span(30, 36)])]
    >>> spans = normalize_spans(spans)
    >>> print(spans)
    [Span(0, 10), Span(20, 36)]
    """
    all_spans = []
    for span in spans:
        if isinstance(span, AdditionalSpan):
            all_spans += span.replaced_spans
        else:
            all_spans.append(span)

    # merge contiguous spans
    all_spans_merged = [all_spans[0]]
    for span in all_spans[1:]:
        prev_span = all_spans_merged[-1]
        if span.start == prev_span.end:
            merged_span = Span(prev_span.start, span.end)
            all_spans_merged[-1] = merged_span
        else:
            all_spans_merged.append(span)

    return all_spans_merged
