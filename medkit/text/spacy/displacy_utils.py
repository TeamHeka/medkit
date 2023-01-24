__all__ = ["medkit_doc_to_displacy", "segments_to_displacy"]

from typing import Any, Callable, Dict, List, Optional

from medkit.core.text import TextDocument, Segment, span_utils


def medkit_doc_to_displacy(
    medkit_doc: TextDocument,
    segment_labels: Optional[List[str]] = None,
    segment_formatter: Optional[Callable[[Segment], str]] = None,
    max_gap_length: int = 3,
) -> Dict[str, Any]:
    """Build data dict that can be passed to `displacy.render()`
    (with `manual=True` and `style="ent"`) to vizualize entities of
    a document.

    Parameters
    ----------
    medkit_doc:
        Document to visualize.
    segment_labels:
        Labels of segments to display. If `None`, all entities are displayed (but
        not segments).
    segment_formatter:
        Optional function returning the text to display as label for a given
        segment. If `None`, the segment label will be used. Can be used for
        instance to display normalization information available in entity or
        segment attributes.
    max_gap_length:
        When cleaning up gaps in spans, spans around gaps smaller than `max_gap_length`
        will be merged.
        Cf :func:`~medkit.core.text.span_utils.clean_up_gaps_in_normalized_spans()`.

    Returns
    -------
    Dict[str, Any]
        Data to be passed to `displacy.render()` as `docs` argument
        (with `manual=True` and `style="ent"`)
    """

    if segment_labels:
        segments = [
            e for label in segment_labels for e in medkit_doc.anns.get(label=label)
        ]
        if not all(isinstance(s, Segment) for s in segments):
            raise ValueError(
                "Cannot display with displacy annotations that are not subclasses of"
                " Segment, make sure that you have provided labels only referring to"
                " segments or entities"
            )
    else:
        segments = medkit_doc.anns.get_entities()

    return segments_to_displacy(
        segments, medkit_doc.text, segment_formatter, max_gap_length
    )


def segments_to_displacy(
    segments: List[Segment],
    raw_text: str,
    segment_formatter: Optional[Callable[[Segment], str]] = None,
    max_gap_length: int = 3,
) -> Dict[str, Any]:
    """Build data dict that can be passed to `displacy.render()`
    (with `manual=True` and `style="ent"`) to vizualize entities.

    Parameters
    ----------
    segments:
        Segments (and/or entities) to visualize in text context.
    raw_text:
        Initial document text from which entities where extracted and to which they spans refer
        (typically the `text` attribute of a :class:`~medkit.core.text.document.TextDocument`).
    segment_formatter:
        Optional function returning the text to display as label for a given
        segment. If `None`, the segment label will be used. Can be used for
        instance to display normalization information available in entity or
        segment attributes.
    max_gap_length:
        When cleaning up gaps in spans, spans around gaps smaller than `max_gap_length`
        will be merged.
        Cf :func:`~medkit.core.text.span_utils.clean_up_gaps_in_normalized_spans()`.

    Returns
    -------
    Dict[str, Any]
        Data to be passed to `displacy.render()` as `docs` argument
        (with `manual=True` and `style="ent"`)
    """
    ents_data = []

    for segment in segments:
        normalized_spans = span_utils.normalize_spans(segment.spans)
        # normalized spans can be empty if spans contained ModifiedSpan with no replaced_spans
        if not normalized_spans:
            continue

        # merge close spans
        cleaned_spans = span_utils.clean_up_gaps_in_normalized_spans(
            normalized_spans, raw_text, max_gap_length=max_gap_length
        )

        # generate text label
        if segment_formatter:
            label = segment_formatter(segment)
        else:
            label = segment.label

        ents_data += [
            {"start": span.start, "end": span.end, "label": label}
            for span in cleaned_spans
        ]

    ents_data = sorted(ents_data, key=lambda d: d["start"])
    return {"text": raw_text, "ents": ents_data}
