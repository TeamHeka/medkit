__all__ = ["SpacyInputConverter", "SpacyOutputConverter"]
import warnings
from typing import List, Optional, Union

from medkit.core import Collection, OperationDescription, ProvBuilder, generate_id
from medkit.core.text import TextDocument
from medkit.text.spacy import (
    build_spacy_doc_from_medkit,
    extract_anns_and_attrs_from_spacy_doc,
)

from spacy import Language
from spacy.tokens import Doc


class SpacyInputConverter:
    """Class in charge of converting spacy documents into a collection of TextDocuments."""

    def __init__(
        self,
        labels_ents_to_transfer: Optional[List[str]] = None,
        name_spans_to_transfer: Optional[List[str]] = None,
        attrs_to_transfer: Optional[List[str]] = None,
        proc_id: Optional[str] = None,
    ):
        """Initialize the spacy input converter

        Parameters
        ----------
        spacy_labels_ents_to_transfer:
            Labels of spacy entities (`doc.ents`) to convert into medkit entities.
            If `None` (default) all spacy entities will be converted and added into
            its origin medkit document.
        spacy_name_spans_to_transfer:
            Name of groups of spacy spans (`doc.spans`) to convert into medkit segments.
            If `None` (default) all groups of spacy spans will be converted and added into
            the medkit document.
        spacy_attrs_to_transfer:
            Name of span extensions to convert into medkit attributes.
            If `None` (default) all non-None extensions will be added for each annotation
        proc_id:
            Identifier of the converter
        """

        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self._prov_builder: Optional[ProvBuilder] = None

        self.labels_ents_to_transfer = labels_ents_to_transfer
        self.name_spans_to_transfer = name_spans_to_transfer
        self.attrs_to_transfer = attrs_to_transfer

    @property
    def description(self) -> OperationDescription:
        config = dict(
            labels_ents_to_transfer=self.labels_ents_to_transfer,
            name_spans_to_transfer=self.name_spans_to_transfer,
            attrs_to_transfer=self.attrs_to_transfer,
        )

        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def load(self, spacy_docs: List[Doc]) -> Collection:
        """
        Create a Collection of TextDocuments from a list of spacy Doc objects.
        Depending on the configuration of the converted, the selected annotations
        and attributes are included in the documents.

        Parameters
        ----------
        spacy_docs:
            A list of spacy documents to convert

        Returns
        -------
        Collection
            A collection of TextDocuments
        """
        medkit_docs = []
        for spacy_doc in spacy_docs:
            # create a new medkit document (TextDocument object)
            medkit_doc = TextDocument(text=spacy_doc.text_with_ws)

            # get anns and attributes from spacy
            anns, attrs_by_ann_id = extract_anns_and_attrs_from_spacy_doc(
                spacy_doc=spacy_doc,
                doc_segment=None,
                labels_ents_to_transfer=self.labels_ents_to_transfer,
                name_spans_to_transfer=self.name_spans_to_transfer,
                attrs_to_transfer=self.attrs_to_transfer,
            )
            # add annotations
            for ann in anns:
                medkit_doc.add_annotation(ann)
                if self._prov_builder is not None:
                    # the input converter does not know the source data item
                    self._prov_builder.add_prov(
                        ann, self.description, source_data_items=[]
                    )

            # add new attributes in each annotation
            for ann_id, attrs in attrs_by_ann_id.items():
                ann = medkit_doc.get_annotation_by_id(ann_id)

                for attr in attrs:
                    ann.attrs.append(attr)
                    if self._prov_builder is not None:
                        # the input converter does not know the source data item
                        self._prov_builder.add_prov(
                            attr, self.description, source_data_items=[]
                        )

            medkit_docs.append(medkit_doc)

        return Collection(medkit_docs)


class SpacyOutputConverter:
    """Class in charge of converting a list/Collection of TextDocuments into a
    list of spacy documents"""

    def __init__(
        self,
        nlp: Language,
        apply_nlp_spacy: bool = False,
        labels_to_transfer: Optional[List[str]] = None,
        attrs_to_transfer: Optional[List[str]] = None,
        proc_id: Optional[str] = None,
    ):
        """Initialize the spacy output converter

        Parameters
        ----------
        nlp:
            Language object with the loaded pipeline from Spacy
        apply_nlp_spacy:
            If True, each component of `nlp` pipeline is applied to the new spacy document.
            Some features, such as 'POS TAG', are added by a component of the pipeline, this
            parameter should be True, in order to add such attributes.
            If False, the `nlp` pipeline is not applied in the spacy document, so the document
            contains only the annotations and attributes transferred by medkit.
        labels_to_transfer:
            Labels of medkit annotations to include in the spacy document.
            If `None` (default) all the annotations will be included.
        attrs_to_transfer:
            Labels of medkit attributes to add in the annotations that will be included.
            If `None` (default) all the attributes will be added as `custom attributes`
            in each annotation included.
        proc_id:
            Identifier of the pipeline

        """
        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self._prov_builder: Optional[ProvBuilder] = None

        self.nlp = nlp
        self.labels_to_transfer = labels_to_transfer
        self.attrs_to_transfer = attrs_to_transfer
        self.apply_nlp_spacy = apply_nlp_spacy

    def convert(self, medkit_docs: Union[List[TextDocument], Collection]) -> List[Doc]:
        """
        Convert a Collection of TextDocuments into a list of spacy Doc objects.
        Depending on the configuration of the converted, the selected annotations
        and attributes are included in the documents.

        Parameters
        ----------
        medkit_docs:
            A list or a collection of TextDocuments to convert

        Returns
        -------
        Collection
            A list of spacy Doc objects
        """

        if isinstance(medkit_docs, Collection):
            medkit_docs = medkit_docs.documents

        spacy_docs = []
        for medkit_doc in medkit_docs:
            if medkit_doc.text is not None:
                # get reference annotation from the medkit document
                raw_text_annotation = medkit_doc.get_annotations_by_label(
                    medkit_doc.RAW_TEXT_LABEL
                )[0]
                # create a spacy document from medkit with the selected annotations
                spacy_doc = build_spacy_doc_from_medkit(
                    nlp=self.nlp,
                    segment=raw_text_annotation,
                    annotations=medkit_doc.get_annotations(),
                    labels_to_transfer=self.labels_to_transfer,
                    attrs_to_transfer=self.attrs_to_transfer,
                )
                # each component of nlp spacy is applied
                if self.apply_nlp_spacy:
                    for _, component in self.nlp.pipeline:
                        spacy_doc = component(spacy_doc)

                spacy_docs.append(spacy_doc)
            else:
                warnings.warn(
                    f"The document with id {medkit_doc.id} has no text, it is not converted"
                )

        return spacy_docs
