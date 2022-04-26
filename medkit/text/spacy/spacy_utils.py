__all__ = [
    "extract_anns_and_attrs_from_spacy_doc",
    "build_spacy_doc_from_medkit_doc",
    "build_spacy_doc_from_medkit_segment",
]
import warnings
from typing import Dict, List, Optional, Tuple


from medkit.core import Attribute
from medkit.core.text import Segment, TextAnnotation, span_utils, Entity
from medkit.core.text.document import TextDocument
from medkit.core.text.span import AnySpanType
from medkit.core.text.span import Span as MedkitSpan

from spacy import Language
from spacy.tokens import Doc, Span
from spacy.tokens.underscore import Underscore
from spacy.util import filter_spans

# change to always show warning messages
warnings.filterwarnings("always", category=UserWarning)


def extract_anns_and_attrs_from_spacy_doc(
    spacy_doc: Doc,
    medkit_source_ann: Optional[Segment] = None,
    labels_ents_to_transfer: Optional[List[str]] = None,
    name_spans_to_transfer: Optional[List[str]] = None,
    attrs_to_transfer: Optional[List[str]] = None,
    rebuild_medkit_anns: bool = False,
) -> Tuple[List[Segment], Dict[str, List[Attribute]]]:
    """Given a spacy document, identify the new spans and create
    the equivalent segments. For each span present in the document,
    extracts the new attributes.

    Parameters
    ----------
    spacy_doc:
         A Spacy Doc with spans to be converted
    doc_segment:
        Segment used to generate the spacy document, useful to be the reference annotation
    labels_ents_to_transfer:
        Labels of entities to be extracted
        If `None` (default) all new entities will be extracted as annotations
    name_spans_to_transfer:
        Name of span groups to be extracted
        If `None` (default) all new spans will be extracted as annotations
    attrs_to_transfer:
        Labels of attributes to extract from the annotations that will be included.
        If `None` (default) all the attributes will be extracted

    Returns
    -------
    annotations: List[Segment]
        New segments extracted from the spacy Doc object
    attributes_by_ann: Dict[str, List[Attribute]]]
        New attributes extracted for each annotation, the key is the annotation id

    Raises
    ------
    ValueError
        Raises when the given medkit source and the spacy doc do not have the same medkit id
    """

    # extensions to indicate the medkit origin
    _define_default_extensions()

    if spacy_doc._.get("medkit_id") is not None:
        if medkit_source_ann is not None and medkit_source_ann.id != spacy_doc._.get(
            "medkit_id"
        ):
            msg = (
                f"The medkit id of the Doc object is {spacy_doc._.get('medkit_id')},"
                " the medkit source annotation provided has a different id:"
                f" {medkit_source_ann.id}."
            )
            raise ValueError(msg)

    # get annotations according to labels_ents_to_transfer and name_spans_to_transfer
    selected_ents = _filter_ents_by_label(spacy_doc, labels_ents_to_transfer)
    selected_spans = _filter_spans_by_label(spacy_doc, name_spans_to_transfer)
    selected_attrs_spacy = _get_defined_spacy_attrs(exclude_medkit_attrs=True)

    if attrs_to_transfer is not None:
        # filter attributes by label
        selected_attrs_spacy = [
            attr for attr in selected_attrs_spacy if attr in attrs_to_transfer
        ]

    new_annotations = []
    new_attributes_by_ann = dict()

    # convert spacy entities
    for entity_spacy in selected_ents:
        medkit_id = entity_spacy._.get("medkit_id")

        if medkit_id is None or rebuild_medkit_anns:
            # create a new entity annotation
            label = entity_spacy.label_
            text, spans = _get_text_and_spans_from_span_spacy(
                span_spacy=entity_spacy, medkit_source_ann=medkit_source_ann
            )

            entity = Entity(label=label, spans=spans, text=text, attrs=[])
            medkit_id = entity.id
            new_annotations.append(entity)

        # for each spacy extension having a value other than None,
        # a medkit Attribute is created
        new_attributes = [
            Attribute(label=attr, value=entity_spacy._.get(attr))
            for attr in selected_attrs_spacy
            if entity_spacy._.get(attr) is not None
        ]

        if new_attributes:
            new_attributes_by_ann[medkit_id] = new_attributes

    # convert spacy span groups
    for label, spans in selected_spans.items():
        for span_spacy in spans:
            medkit_id = span_spacy._.get("medkit_id")

            if medkit_id is None or rebuild_medkit_anns:
                # create new segment annotation
                text, spans = _get_text_and_spans_from_span_spacy(
                    span_spacy=span_spacy, medkit_source_ann=medkit_source_ann
                )
                segment = Segment(label=label, spans=spans, text=text, attrs=[])
                medkit_id = segment.id
                new_annotations.append(segment)

            # for each spacy extension having a value other than None,
            # a medkit Attribute is created
            new_attributes = [
                Attribute(label=attr, value=span_spacy._.get(attr))
                for attr in selected_attrs_spacy
                if span_spacy._.get(attr) is not None
            ]

            if new_attributes:
                new_attributes_by_ann[medkit_id] = new_attributes

    return new_annotations, new_attributes_by_ann


def build_spacy_doc_from_medkit_doc(
    nlp: Language,
    medkit_doc: TextDocument,
    labels_to_transfer: Optional[List[str]] = None,
    attrs_to_transfer: Optional[List[str]] = None,
    include_medkit_info: bool = True,
) -> Doc:
    """Create a Spacy Doc from a TextDocument.

    Parameters
    ----------
    nlp:
        Language object with the loaded pipeline from Spacy
    medkit_doc:
        TextDocument to convert
    labels_to_transfer:
        Labels of annotations to include in the spacy document.
        If `None` (default) all the annotations will be included.
    attrs_to_transfer:
        Labels of attributes to add in the annotations that will be included.
        If `None` (default) all the attributes will be added as `custom attributes`
        in each annotation included.
    include_medkit_info:
        If True, medkitID and spans are included as extensions in the Doc object
        to identify the medkit source annotation.
        If False, no information about IDs or spans is included.

    Returns
    -------
    Doc:
        A Spacy Doc with the selected annotations included.
    """
    assert isinstance(nlp, Language), "'nlp' should be a Language instance from Spacy"
    # extensions to indicate the medkit origin
    _define_default_extensions()

    # get the raw text segment to transfer
    raw_text_segment = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]
    annotations = medkit_doc.get_annotations()

    if labels_to_transfer is not None:
        # filter annotations by label
        annotations = [ann for ann in annotations if ann.label in labels_to_transfer]

    # create a spacy doc
    doc = build_spacy_doc_from_medkit_segment(
        nlp=nlp,
        segment=raw_text_segment,
        annotations=annotations,
        attrs_to_transfer=attrs_to_transfer,
        include_medkit_info=include_medkit_info,
    )

    if labels_to_transfer and annotations == []:
        # labels_to_transfer were a list but none of the annotations
        # had a label of interest
        _labels = ",".join(labels_to_transfer)
        warnings.warn(
            f"No medkit annotations were included because none have '{_labels}' as"
            " label."
        )

    return doc


def build_spacy_doc_from_medkit_segment(
    nlp: Language,
    segment: Segment,
    annotations: Optional[List[TextAnnotation]] = None,
    attrs_to_transfer: Optional[List[str]] = None,
    include_medkit_info: bool = True,
) -> Doc:
    """Create a Spacy Doc from a Segment.

    Parameters
    ----------
    nlp:
        Language object with the loaded pipeline from Spacy
    segment:
        Segment to convert, this annotation contains the text to convert
    annotations:
        List of annotations in the segment of interest
    attrs_to_transfer:
        Labels of attributes to add in the annotations that will be included.
        If `None` (default) all the attributes will be added as `custom attributes`
        in each annotation included.
    include_medkit_info:
        If True, medkitID and spans are included as extensions in the Doc object
        to identify the medkit source annotation.
        If False, no information about IDs or spans is included.

    Returns
    -------
    Doc:
        A Spacy Doc with the selected annotations included.
    """
    assert isinstance(nlp, Language), "'nlp' should be a Language instance from Spacy"

    # extensions to indicate the medkit origin
    _define_default_extensions()

    # create spacy doc
    doc = nlp.make_doc(segment.text)
    if include_medkit_info:
        doc._.set("medkit_id", segment.id)
        doc._.set("medkit_spans", segment.spans)

    if annotations is None:
        annotations = []

    if annotations:
        if attrs_to_transfer is None:
            # get a list of attrs_to_transfer from selected annotations
            attrs_to_transfer = list(
                set([attr.label for ann in annotations for attr in ann.attrs])
            )
        _define_attrs_extensions(attrs_to_transfer)

        # include annotations in the document and set attributes as extensions
        doc = _add_entities_in_spacy_doc(
            spacy_doc=doc,
            annotations=annotations,
            attrs_to_transfer=attrs_to_transfer,
            include_medkit_info=include_medkit_info,
        )
        doc = _add_segments_in_spacy_doc(
            spacy_doc=doc,
            annotations=annotations,
            attrs_to_transfer=attrs_to_transfer,
            include_medkit_info=include_medkit_info,
        )

    return doc


def _get_defined_spacy_attrs(exclude_medkit_attrs: bool = False) -> List[str]:
    """Returns the name of the custom attributes
    configured in spacy spans.

    Parameters
    ----------
    exclude_medkit_attrs:
        If True, medkit attrs (medkit_id, and attrs transfered from medkit) are excluded

    Returns
    -------
    List[str]:
        Name of spans extensions defined in Spacy
    """
    attrs_default = set(("medkit_id", "medkit_spans"))

    # `get_state` is a spacy function, it returns a tuple of dictionaries
    # with the information of the defined extensions
    # where ([0]= token_extensions,[1]=span_extensions,[2]=doc_extensions)
    available_attrs = Underscore.get_state()[1].keys()

    attrs_spacy = []
    if exclude_medkit_attrs:
        # remove default medkit attributes
        attrs = [attr for attr in available_attrs if attr not in attrs_default]

        # remove attributes defined by medkit
        seen_attrs = []
        for attr in attrs:
            if attr.endswith("_") and attr[:-1] in attrs:
                # if `attr` is a medkit attribute, `attr` and `attr_` are extensions
                # these are not spacy attrs, so, they are discarted
                seen_attrs += [attr[:-1], attr]
            elif attr not in seen_attrs:
                # `attr` is not a medkit attribute
                attrs_spacy.append(attr)
    else:
        attrs_spacy = list(available_attrs)

    return attrs_spacy


def _define_spacy_span_extension(custom_attr: str):
    if not Span.has_extension(custom_attr):
        Span.set_extension(custom_attr, default=None)


def _define_spacy_doc_extension(custom_attr: str):
    if not Doc.has_extension(custom_attr):
        Doc.set_extension(custom_attr, default=None)


def _define_default_extensions():
    """Define default attributes to identify origin from medkit"""
    _define_spacy_doc_extension("medkit_id")
    _define_spacy_doc_extension("medkit_spans")
    _define_spacy_span_extension("medkit_id")


def _define_attrs_extensions(attrs_to_transfer: List[str]):
    """Define attributes as span extensions in the Spacy context."""
    for attr in attrs_to_transfer:
        # `attr_` is the ID_medkit of the original attribute
        _define_spacy_span_extension(f"{attr}_")
        _define_spacy_span_extension(attr)


def _simplify_medkit_spans(spans: List[AnySpanType]) -> Tuple[int, int]:
    """Return a single span from a list of spans"""

    spans_norm: List[MedkitSpan] = span_utils.normalize_spans(spans)

    if len(spans_norm) > 1:
        # Spacy does not allow discontinuous spans
        # for compatibility, get a continuous span from the list
        start = min(spans_norm).start
        end = max(spans_norm).end
        span = MedkitSpan(start, end)
        warnings.warn(
            f"These spans {spans} are discontinuous, they were converted"
            f" into its expanded version, from {start} to {end}."
        )
    else:
        span = spans_norm[0]

    return span


def _segment_to_spacy_span(
    spacy_doc_target: Doc,
    medkit_segment: Segment,
    attrs_to_transfer: List[str],
    include_medkit_info: bool,
) -> Span:
    """Create a spacy span given a medkit segment."""
    # get a single span
    start, end = _simplify_medkit_spans(medkit_segment.spans)
    # create a spacy span from characters in the text instead of tokens
    span = spacy_doc_target.char_span(
        start, end, alignment_mode="expand", label=medkit_segment.label
    )

    if include_medkit_info:
        span._.set("medkit_id", medkit_segment.id)

    # TBD: In medkit having an attribute, indicates that the attribute exists
    # for the given annotation, so for the moment, we force True as value
    for attr in medkit_segment.attrs:
        if attr.label in attrs_to_transfer:
            # set attributes as extensions
            span._.set(attr.label, True if attr.value is None else attr.value)
            if include_medkit_info:
                span._.set(f"{attr.label}_", attr.id)

    return span


def _get_text_and_spans_from_span_spacy(
    span_spacy: Span, medkit_source_ann: Optional[Segment]
) -> Tuple[str, List[AnySpanType]]:
    """Return text and spans depending on the origin of the spacy span"""

    if medkit_source_ann is None:
        text = span_spacy.text
        spans = [MedkitSpan(span_spacy.start_char, span_spacy.end_char)]
    else:
        # the origin is a medkit annotation
        text, spans = span_utils.extract(
            medkit_source_ann.text,
            medkit_source_ann.spans,
            [(span_spacy.start_char, span_spacy.end_char)],
        )
    return text, spans


def _add_entities_in_spacy_doc(
    spacy_doc: Doc,
    annotations: List[Segment],
    attrs_to_transfer: List[str],
    include_medkit_info: bool,
) -> Doc:
    """Convert entities into spacy spans and modifies
    the entities in the Doc object (doc.ents)"""
    entities = []
    for ann in annotations:
        if isinstance(ann, Entity):
            spacy_span = _segment_to_spacy_span(
                spacy_doc_target=spacy_doc,
                medkit_segment=ann,
                attrs_to_transfer=attrs_to_transfer,
                include_medkit_info=include_medkit_info,
            )
            entities.append(spacy_span)

    ents_filtered = filter_spans(entities)
    # TBD: we could include discarded entities in a span group called 'discarded'
    ents_no_transferred = ",".join(
        [f"({ent.text})" for ent in entities if ent not in ents_filtered]
    )
    if ents_no_transferred:
        warnings.warn(
            f"Spacy does not allow entity overlapping: '{ents_no_transferred}' were"
            " discarded."
        )
    spacy_doc.ents = list(spacy_doc.ents) + ents_filtered
    return spacy_doc


def _add_segments_in_spacy_doc(
    spacy_doc: Doc,
    annotations: List[Segment],
    attrs_to_transfer: List[str],
    include_medkit_info: bool,
) -> Doc:
    """Convert segments into a spacy spans and modifies
    the spans in the Doc object (doc.spans)"""

    for ann in annotations:
        if isinstance(ann, Segment) and not isinstance(ann, Entity):
            # create spacy span
            spacy_span = _segment_to_spacy_span(
                spacy_doc_target=spacy_doc,
                medkit_segment=ann,
                attrs_to_transfer=attrs_to_transfer,
                include_medkit_info=include_medkit_info,
            )

            # add in the spacy doc
            if ann.label not in spacy_doc.spans.keys():
                spacy_doc.spans[ann.label] = [spacy_span]
            else:
                spacy_doc.spans[ann.label].append(spacy_span)

    return spacy_doc


def _filter_ents_by_label(
    spacy_doc: Doc, labels_ents_to_transfer: Optional[List[str]] = None
) -> List[Span]:
    ents = []
    if labels_ents_to_transfer is None:
        ents = list(spacy_doc.ents)
    else:
        ents = [
            ent
            for label in labels_ents_to_transfer
            for ent in spacy_doc.ents
            if ent.label_ == label
        ]
    return ents


def _filter_spans_by_label(
    spacy_doc: Doc, name_spans_to_transfer: Optional[List[str]] = None
) -> Dict[str, List[Span]]:
    spans = dict()
    if name_spans_to_transfer is None:
        spans = dict(spacy_doc.spans)
    else:
        spans = {
            label: sp
            for label, sp in spacy_doc.spans.items()
            if label in name_spans_to_transfer
        }
    return spans
