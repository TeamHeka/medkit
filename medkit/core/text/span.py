__all__ = ["Span", "remove", "extract"]

from typing import List, NamedTuple, Tuple


class Span(NamedTuple):
    start: int
    end: int

    @property
    def length(self):
        return self.end - self.start


def remove(
    text: str,
    spans: List[Span],
    ranges: List[Tuple[int, int]],
) -> Tuple[str, List[Span]]:
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
    output_spans = []

    # current span and associated values
    span_index = 0
    span = spans[0]
    # start and end in "relative" coords (can be compared to range start/end)
    span_start = 0
    span_end = span.length

    # current range to remove and associated values
    range_index = 0
    range_start, range_end = ranges[0]

    while span_index < len(spans) or range_index < len(ranges):
        # iterate to next range if current range has been fully handled
        if range_index < len(ranges) and range_end <= span_start:
            # move on to next span if we haven't reached end of ranges
            # and updated associated values
            range_index += 1
            if range_index < len(ranges):
                range_start, range_end = ranges[range_index]

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

        # create span for the part before the range
        # and add it to output
        if length_before_range > 0:
            before_span = Span(start=span.start, end=span.start + length_before_range)
            output_spans.append(before_span)

        # create span for the remaining part after the range
        # and use it as current span
        if length_after_range > 0:
            span = Span(start=span.end - length_after_range, end=span.end)
        # update span_start to point to the begining of the remainder
        span_start = span_end - length_after_range

    return output_spans


def extract(
    text: str,
    spans: List[Span],
    ranges: List[Tuple[int, int]],
) -> Tuple[str, List[Span]]:
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
