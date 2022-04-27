__all__ = ["SpacyPipeline"]
from typing import List, Optional
import dataclasses
from medkit.core import OperationDescription, ProvBuilder, generate_id
from medkit.core.text import Segment
from medkit.text.spacy import spacy_utils

from spacy import Language
from spacy.tokens import Doc


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    # TODO: transfer of annotations and attributes attached to
    # a segment are not currently supported, no anns are included
    medkit_labels_to_transfer = []
    medkit_attrs_to_transfer = []


class SpacyPipeline:
    """Segment annotator relying on a Spacy pipeline"""

    def __init__(
        self,
        nlp: Language,
        medkit_labels_to_transfer: Optional[
            List[str]
        ] = DefaultConfig.medkit_labels_to_transfer,
        medkit_attrs_to_transfer: Optional[
            List[str]
        ] = DefaultConfig.medkit_attrs_to_transfer,
        spacy_labels_ents_to_transfer: Optional[List[str]] = None,
        spacy_name_spans_to_transfer: Optional[List[str]] = None,
        spacy_attrs_to_transfer: Optional[List[str]] = None,
        proc_id: Optional[str] = None,
    ):
        """Initialize the segment annotator

        Parameters
        ----------
        nlp:
            Language object with the loaded pipeline from Spacy
        medkit_labels_to_transfer:
            Labels of medkit annotations to include in the spacy document.
            Default: [] (cf.DefaultConfig) no annotations are included
        medkit_attrs_to_transfer:
            Labels of medkit attributes to add in the annotations that will be included.
            Default: [] (cf.DefaultConfig) no annotations are included
        spacy_labels_ents_to_transfer:
            Labels of new spacy entities (`doc.ents`) to convert into medkit entities.
            If `None` (default) all the new spacy entities will be converted and added into
            its origin medkit document.
        spacy_name_spans_to_transfer:
            Name of new spacy span groups (`doc.spans`) to convert into medkit segments.
            If `None` (default) new spacy span groups will be converted and added into
            its origin medkit document.
        spacy_attrs_to_transfer:
            Name of span extensions to convert into medkit attributes.
            If `None` (default) all non-None extensions will be added for each annotation with
            a medkit ID.
        proc_id:
            Identifier of the pipeline
        """
        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self._prov_builder: Optional[ProvBuilder] = None
        self._include_medkit_info = True
        self._rebuild_medkit_anns = False

        # TODO:create nlp from config
        self.nlp = nlp
        self.medkit_labels_to_transfer = medkit_labels_to_transfer
        self.medkit_attrs_to_transfer = medkit_attrs_to_transfer
        self.spacy_labels_ents_to_transfer = spacy_labels_ents_to_transfer
        self.spacy_name_spans_to_transfer = spacy_name_spans_to_transfer
        self.spacy_attrs_to_transfer = spacy_attrs_to_transfer

    @property
    def description(self) -> OperationDescription:
        # TBD: use nlp.config
        config = dict(
            nlp=self.nlp.config["nlp"],
            medkit_labels_to_transfer=self.medkit_labels_to_transfer,
            medkit_attrs_to_transfer=self.medkit_attrs_to_transfer,
            spacy_labels_ents_to_transfer=self.spacy_labels_ents_to_transfer,
            spacy_name_spans_to_transfer=self.spacy_name_spans_to_transfer,
            spacy_attrs_to_transfer=self.spacy_attrs_to_transfer,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def run(self, segments: List[Segment]) -> List[Segment]:
        """Run a spacy pipeline on a list of segments provided as input
        and returns a new list of segments.
        Each segment is converted to spacy document (Doc object).
        Then, the spacy pipeline is executed and finally, the new
        annotations and attributes are converted into medkit annotations.

        Parameters
        ----------
        segments:
            List of segments on which to run the spacy pipeline

        Returns
        -------
        List[Segments]:
            List of new annotations
        """
        for segment in segments:
            # build spacy doc
            # no annotations are included
            spacy_doc = spacy_utils.build_spacy_doc_from_medkit_segment(
                nlp=self.nlp,
                segment=segment,
                annotations=[],
                attrs_to_transfer=self.medkit_attrs_to_transfer,
            )
            # apply nlp spacy
            spacy_doc = self.nlp(spacy_doc)

            return [
                new_segment
                for segment in segments
                for new_segment in self._find_segments_in_spacy_doc(
                    spacy_doc=spacy_doc, medkit_source_ann=segment
                )
            ]

    def _find_segments_in_spacy_doc(self, spacy_doc: Doc, medkit_source_ann: Segment):
        # get new annotations and attributes
        segments, attrs_by_ann_id = spacy_utils.extract_anns_and_attrs_from_spacy_doc(
            spacy_doc=spacy_doc,
            medkit_source_ann=medkit_source_ann,
            labels_ents_to_transfer=self.spacy_labels_ents_to_transfer,
            name_spans_to_transfer=self.spacy_name_spans_to_transfer,
            attrs_to_transfer=self.spacy_attrs_to_transfer,
            rebuild_medkit_anns=self._rebuild_medkit_anns,
        )
        for new_segment in segments:
            # add provenance
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    new_segment,
                    self.description,
                    source_data_items=[medkit_source_ann],
                )

            # add attributes
            if new_segment.id in attrs_by_ann_id.keys():
                for attr in attrs_by_ann_id[new_segment.id]:
                    new_segment.attrs.append(attr)
                    if self._prov_builder is not None:
                        self._prov_builder.add_prov(
                            attr, self.description, source_data_items=[new_segment]
                        )

            yield new_segment
