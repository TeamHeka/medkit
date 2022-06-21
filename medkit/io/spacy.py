__all__ = ["SpacyInputConverter", "SpacyOutputConverter"]
import warnings
from typing import List, Optional, Union

from spacy import Language
from spacy.tokens import Doc

from medkit.core import Collection, OperationDescription, ProvBuilder, generate_id
from medkit.core.text import TextDocument
from medkit.text.spacy.spacy_utils import (
    build_spacy_doc_from_medkit_doc,
    extract_anns_and_attrs_from_spacy_doc,
)


class SpacyInputConverter:
    """Class in charge of converting spacy documents into a collection of TextDocuments."""

    def __init__(
        self,
        entities: Optional[List[str]] = None,
        span_groups: Optional[List[str]] = None,
        attrs: Optional[List[str]] = None,
        op_id: Optional[str] = None,
    ):
        """Initialize the spacy input converter

        Parameters
        ----------
        entities:
            Labels of spacy entities (`doc.ents`) to convert into medkit entities.
            If `None` (default) all spacy entities will be converted and added into
            its origin medkit document.
        span_groups:
            Name of groups of spacy spans (`doc.spans`) to convert into medkit segments.
            If `None` (default) all groups of spacy spans will be converted and added into
            the medkit document.
        attrs:
            Name of span extensions to convert into medkit attributes.
            If `None` (default) all non-None extensions will be added for each annotation
        op_id:
            Identifier of the converter
        """

        if op_id is None:
            op_id = generate_id()

        self.id = op_id
        self._prov_builder: Optional[ProvBuilder] = None

        self.entities = entities
        self.span_groups = span_groups
        self.attrs = attrs

    @property
    def description(self) -> OperationDescription:
        config = dict(
            entities=self.entities,
            span_groups=self.span_groups,
            attrs=self.attrs,
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
            anns = self._load_anns(spacy_doc)
            for ann in anns:
                medkit_doc.add_annotation(ann)
            medkit_docs.append(medkit_doc)

        return Collection(medkit_docs)

    @classmethod
    def from_description(cls, description: OperationDescription):
        return cls(op_id=description.id, **description.config)

    def _load_anns(self, spacy_doc: Doc):
        annotations, attributes_by_ann = extract_anns_and_attrs_from_spacy_doc(
            spacy_doc=spacy_doc,
            medkit_source_ann=None,
            entities=self.entities,
            span_groups=self.span_groups,
            attrs=self.attrs,
            rebuild_medkit_anns_and_attrs=True,
        )

        # add annotations
        for ann in annotations:
            if self._prov_builder is not None:
                # the input converter does not know the source data item
                self._prov_builder.add_prov(ann, self.description, source_data_items=[])

            if ann.id in attributes_by_ann.keys():
                attrs = attributes_by_ann[ann.id]
                for attr in attrs:
                    ann.attrs.append(attr)
                    if self._prov_builder is not None:
                        # the input converter does not know the source data item
                        self._prov_builder.add_prov(
                            attr, self.description, source_data_items=[]
                        )
        return annotations


class SpacyOutputConverter:
    """Class in charge of converting a list/Collection of TextDocuments into a
    list of spacy documents"""

    def __init__(
        self,
        nlp: Language,
        apply_nlp_spacy: bool = False,
        labels_anns: Optional[List[str]] = None,
        attrs: Optional[List[str]] = None,
        op_id: Optional[str] = None,
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
        labels_anns:
            Labels of medkit annotations to include in the spacy document.
            If `None` (default) all the annotations will be included.
        attrs:
            Labels of medkit attributes to add in the annotations that will be included.
            If `None` (default) all the attributes will be added as `custom attributes`
            in each annotation included.
        op_id:
            Identifier of the pipeline

        """
        if op_id is None:
            op_id = generate_id()

        self.id = op_id
        self._prov_builder: Optional[ProvBuilder] = None

        self.nlp = nlp
        self.labels_anns = labels_anns
        self.attrs = attrs
        self.apply_nlp_spacy = apply_nlp_spacy

    @property
    def description(self) -> OperationDescription:
        # medkit does not support serialisation of nlp objects,
        # however version information like model name, author etc. is stored
        config = dict(
            nlp_metadata=self.nlp.meta,
            labels_anns=self.labels_anns,
            attrs=self.attrs,
            apply_nlp_spacy=self.apply_nlp_spacy,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

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
            medkit_docs = [
                medkit_doc
                for medkit_doc in medkit_docs.documents
                if isinstance(medkit_doc, TextDocument)
            ]

        spacy_docs = []
        for medkit_doc in medkit_docs:
            if medkit_doc.text is None:
                warnings.warn(
                    f"The document with id {medkit_doc.id} has no text, it is not"
                    " converted"
                )
                continue

            # create a spacy document from medkit with the selected annotations
            spacy_doc = build_spacy_doc_from_medkit_doc(
                nlp=self.nlp,
                medkit_doc=medkit_doc,
                labels_anns=self.labels_anns,
                attrs=self.attrs,
                include_medkit_info=False,
            )
            # each component of nlp spacy is applied
            if self.apply_nlp_spacy:
                spacy_doc = self.nlp(spacy_doc)

            spacy_docs.append(spacy_doc)

        return spacy_docs
