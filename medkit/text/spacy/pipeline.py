__all__ = ["SpacyPipeline"]
from typing import List, Optional

from spacy import Language
from spacy.tokens import Doc

from medkit.core import OperationDescription, ProvBuilder, generate_id
from medkit.core.text import Segment
from medkit.text.spacy import spacy_utils


class SpacyPipeline:
    """Segment annotator relying on a Spacy pipeline"""

    def __init__(
        self,
        nlp: Language,
        spacy_entities: Optional[List[str]] = None,
        spacy_span_groups: Optional[List[str]] = None,
        spacy_attrs: Optional[List[str]] = None,
        proc_id: Optional[str] = None,
    ):
        """Initialize the segment annotator

        Parameters
        ----------
        nlp:
            Language object with the loaded pipeline from Spacy
        spacy_entities:
            Labels of new spacy entities (`doc.ents`) to convert into medkit entities.
            If `None` (default) all the new spacy entities will be converted
        spacy_span_groups:
            Name of new spacy span groups (`doc.spans`) to convert into medkit segments.
            If `None` (default) new spacy span groups will be converted
        spacy_attrs:
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

        self.nlp = nlp
        self.spacy_entities = spacy_entities
        self.spacy_span_groups = spacy_span_groups
        self.spacy_attrs = spacy_attrs

    @property
    def description(self) -> OperationDescription:
        # medkit does not support serialisation of nlp objects,
        # however version information like model name, author etc. is stored
        config = dict(
            nlp_metadata=self.nlp.meta,
            spacy_entities=self.spacy_entities,
            spacy_span_groups=self.spacy_span_groups,
            spacy_attrs=self.spacy_attrs,
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
        output_segments = []
        for segment in segments:
            # build spacy doc
            # TODO: transfer of annotations and attributes attached to
            # a segment are not currently supported, no anns are included
            spacy_doc = spacy_utils.build_spacy_doc_from_medkit_segment(
                nlp=self.nlp,
                segment=segment,
                annotations=[],
                attrs=[],
                include_medkit_info=True,
            )
            # apply nlp spacy
            spacy_doc = self.nlp(spacy_doc)

            new_segments = self._find_segments_in_spacy_doc(
                spacy_doc=spacy_doc, medkit_source_ann=segment
            )
            output_segments.extend(new_segments)

        return output_segments

    def _find_segments_in_spacy_doc(self, spacy_doc: Doc, medkit_source_ann: Segment):
        # get new annotations and attributes
        segments, attrs_by_ann_id = spacy_utils.extract_anns_and_attrs_from_spacy_doc(
            spacy_doc=spacy_doc,
            medkit_source_ann=medkit_source_ann,
            entities=self.spacy_entities,
            span_groups=self.spacy_span_groups,
            attrs=self.spacy_attrs,
            rebuild_medkit_anns_and_attrs=False,
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
                            attr,
                            self.description,
                            source_data_items=[medkit_source_ann],
                        )

            yield new_segment
