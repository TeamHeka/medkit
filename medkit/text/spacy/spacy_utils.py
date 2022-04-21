__all__ = [
    "extract_anns_and_attrs_from_spacy_doc",
    "build_spacy_doc_from_medkit",
    "get_defined_spacy_attrs",
]
import warnings
from typing import Any, Dict, List, Optional, Tuple

from medkit.core import Attribute
from medkit.core.text import Segment, TextAnnotation, span_utils, Entity
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
    doc_segment: Optional[Segment] = None,
    labels_ents_to_transfer: Optional[List[str]] = None,
    name_spans_to_transfer: Optional[List[str]] = None,
    attrs_to_transfer: Optional[List[str]] = None,
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
        Raises when the spacy Doc object came from a Segment but
        that segment was not included as parameter or the segment
        and the spacy doc do not have the same medkit id
    """

    # extensions to indicate the medkit origin
    _define_default_extensions()

    if spacy_doc._.get("medkit_id") is not None:
        if doc_segment is None:
            msg = (
                "The Doc object comes from a medkit segment, it should be included as"
                " `doc_segment`."
            )
            raise ValueError(msg)
        elif doc_segment.id != spacy_doc._.get("medkit_id"):
            msg = (
                f"The medkit id of the Doc object is {spacy_doc._.get('medkit_id')},"
                f" the segment provided has a different id: {doc_segment.id}."
            )
            raise ValueError(msg)

    # get annotations according to labels_ents_to_transfer and name_spans_to_transfer
    # TODO: simplify two list in one list of selected labels
    selected_ents = _filter_ents_by_label(spacy_doc, labels_ents_to_transfer)
    selected_spans = _filter_spans_by_label(spacy_doc, name_spans_to_transfer)
    selected_attrs_spacy = get_defined_spacy_attrs(exclude_medkit_attrs=True)

    if attrs_to_transfer is not None:
        # filter attributes by label
        selected_attrs_spacy = [
            attr for attr in selected_attrs_spacy if attr in attrs_to_transfer
        ]

    annotations = []
    attributes_by_ann = dict()

    for spacy_entity in selected_ents:
        medkit_id = spacy_entity._.get("medkit_id")

        if medkit_id is None:
            # spacy_entity does not come from medkit
            # create a new entity annotation
            label = spacy_entity.label_
            text, spans = _get_text_and_spans_from_span_spacy(spacy_entity, doc_segment)

            entity = Entity(label, spans, text, attrs=[])
            medkit_id = entity.id
            annotations.append(entity)

        # for each spacy extension having a value other than None,
        # a medkit Attribute is created
        new_attributes = [
            Attribute(attr, value=spacy_entity._.get(attr))
            for attr in selected_attrs_spacy
            if spacy_entity._.get(attr) is not None
        ]

        if new_attributes:
            attributes_by_ann[medkit_id] = new_attributes

    for label_to_medkit, spans in selected_spans.items():
        for spacy_span in spans:
            medkit_id = spacy_span._.get("medkit_id")

            if medkit_id is None:
                # spacy_span does not come from medkit
                # create new segment annotation
                label = label_to_medkit
                text, spans = _get_text_and_spans_from_span_spacy(
                    spacy_span, doc_segment
                )

                segment = Segment(label, spans, text, attrs=[])
                medkit_id = segment.id
                annotations.append(segment)

            # for each spacy extension having a value other than None,
            # a medkit Attribute is created
            new_attributes = [
                Attribute(attr, value=spacy_span._.get(attr))
                for attr in selected_attrs_spacy
                if spacy_span._.get(attr) is not None
            ]

            if new_attributes:
                attributes_by_ann[medkit_id] = new_attributes

    return annotations, attributes_by_ann


def build_spacy_doc_from_medkit(
    nlp: Language,
    segment: Segment,
    annotations: Optional[List[TextAnnotation]] = None,
    labels_to_transfer: Optional[List[str]] = None,
    attrs_to_transfer: Optional[List[str]] = None,
) -> Doc:
    """Create a Spacy Doc from a TextDocument.

    Parameters
    ----------
    nlp:
        Language object with the loaded pipeline from Spacy
    segment:
        Segment to convert, this annotation contains the text to convert
    annotations:
        List of annotations in the segment of interest
    labels_to_transfer:
        Labels of annotations to include in the spacy document.
        If `None` (default) all the annotations will be included.
    attrs_to_transfer:
        Labels of attributes to add in the annotations that will be included.
        If `None` (default) all the attributes will be added as `custom attributes`
        in each annotation included.

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
    doc._.set("medkit_id", segment.id)
    doc._.set("medkit_spans", segment.spans)

    selected_annotations = [] if annotations is None else annotations

    if labels_to_transfer is not None:
        # filter annotations by label
        selected_annotations = [
            ann for ann in selected_annotations if ann.label in labels_to_transfer
        ]

    if selected_annotations:
        if attrs_to_transfer is None:
            # get a list of attrs_to_transfer from selected annotations
            attrs_to_transfer = list(
                set([attr.label for ann in selected_annotations for attr in ann.attrs])
            )
        _define_attrs_extensions(attrs_to_transfer)

        # include annotations in the document and set attributes as extensions
        doc = _add_entities_in_spacy_doc(doc, selected_annotations, attrs_to_transfer)
        doc = _add_segments_in_spacy_doc(doc, selected_annotations, attrs_to_transfer)

    elif selected_annotations and labels_to_transfer:
        _labels = ",".join(labels_to_transfer)
        warnings.warn(f"No medkit annotations were found using '{_labels}' as label.")

    return doc


def get_defined_spacy_attrs(exclude_medkit_attrs: bool = False) -> List[str]:
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


def _define_spacy_extension(cls: str, attr: str, default_value: Any):
    if cls == "span":
        if not Span.has_extension(attr):
            Span.set_extension(attr, default=default_value)
    elif cls == "doc":
        if not Doc.has_extension(attr):
            Doc.set_extension(attr, default=default_value)


def _define_default_extensions():
    """Define default attributes to identify origin from medkit"""
    _define_spacy_extension("doc", "medkit_id", None)
    _define_spacy_extension("doc", "medkit_spans", None)
    _define_spacy_extension("span", "medkit_id", None)
    _define_spacy_extension("span", "medkit_spans", None)


def _define_attrs_extensions(attrs_to_transfer: List[str]):
    """Define attributes as span extensions in the Spacy context."""
    for attr in attrs_to_transfer:
        # `attr_` is the ID_medkit of the original attribute
        _define_spacy_extension("span", attr=f"{attr}_", default_value=None)
        _define_spacy_extension("span", attr=attr, default_value=None)


def _simplify_medkit_spans(spans: List[AnySpanType]) -> Tuple[int, int]:
    """Return a single span from a list of spans"""
    spans_norm = span_utils.normalize_spans(spans)
    if len(spans_norm) > 1:
        # it is a discontinuous span, expand the span
        # to obtain a continuous span
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
    spacy_doc: Doc,
    ann: Segment,
    attrs_to_transfer: Optional[List[str]] = None,
) -> Span:
    """Create a spacy span given a medkit segment."""

    # get a single span
    start, end = _simplify_medkit_spans(ann.spans)

    # create a spacy span from characters in the text instead of tokens
    span = spacy_doc.char_span(start, end, alignment_mode="expand", label=ann.label)
    span._.set("medkit_id", ann.id)
    span._.set("medkit_spans", ann.spans)

    # TBD: In medkit having an attribute, indicates that the attribute exists
    # for the given annotation, so for the moment, we force True as value
    for attr in ann.attrs:
        if attr.label in attrs_to_transfer:
            # set attributes as extensions
            if span._.get(f"{attr.label}_") is None:
                # the attribute is not defined
                span._.set(attr.label, True if attr.value is None else attr.value)
                span._.set(f"{attr.label}_", attr.id)
            else:
                first_id = span._.get(f"{attr.label}_")
                warnings.warn(
                    f"The attribute {attr.label} is already defined in the span,"
                    f"only {first_id} is transferred."
                )

    return span


def _get_text_and_spans_from_span_spacy(
    span: Span, doc_segment: Optional[Segment]
) -> Tuple[str, List[AnySpanType]]:
    """Return text and spans depending on the origin of the spacy span"""

    if doc_segment is None:
        text = span.text
        spans = [MedkitSpan(span.start_char, span.end_char)]
    else:
        # the origin is a medkit annotation
        text, spans = span_utils.extract(
            doc_segment.text, doc_segment.spans, [(span.start_char, span.end_char)]
        )
    return text, spans


def _add_entities_in_spacy_doc(
    spacy_doc: Doc,
    annotations: List[Segment],
    attrs_to_transfer: Optional[List[str]] = None,
) -> Doc:
    """Convert entities into spacy spans and modifies
    the entities in the Doc object (doc.ents)"""
    ents = [
        _segment_to_spacy_span(spacy_doc, ann, attrs_to_transfer)
        for ann in annotations
        if isinstance(ann, Entity)
    ]
    ents_filtered = filter_spans(ents)
    ents_no_transferred = ",".join(
        [f"({ent.text})" for ent in ents if ent not in ents_filtered]
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
    attrs_to_transfer: Optional[List[str]] = None,
) -> Doc:
    """Convert segments into a spacy spans and modifies
    the spans in the Doc object (doc.spans)"""

    for ann in annotations:
        if isinstance(ann, Segment) and not isinstance(ann, Entity):
            # create spacy span
            span = _segment_to_spacy_span(spacy_doc, ann, attrs_to_transfer)

            # add in the spacy doc
            if ann.label not in spacy_doc.spans.keys():
                spacy_doc.spans[ann.label] = [span]
            else:
                spacy_doc.spans[ann.label].append(span)

    return spacy_doc


def _filter_ents_by_label(
    spacy_doc: Doc, labels_ents_to_transfer: Optional[List[str]] = None
) -> List[Span]:
    """Return spacy entities that have a label of interest"""
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
    """Return groups of spacy spans that have a label of interest"""
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
