from __future__ import annotations

__all__ = ["SectionTokenizer"]

import dataclasses
import pathlib
import pandas as pd
import yaml
from flashtext import KeywordProcessor
from typing import Dict, List, TYPE_CHECKING

from medkit.core.document import Collection
from medkit.core.processing import ProcessingDescription
from medkit.core.text import Attribute, TextBoundAnnotation, TextDocument
from medkit.core.text import span as span_utils


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label = "SECTION"
    section_dict_path = pathlib.Path(__file__).parent / "default_section_dict.yml"


class SectionTokenizer:
    """Section segmentation annotator based on keyword rules"""

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def __init__(
        self,
        input_label: str,
        output_label: str = DefaultConfig.output_label,
        section_dict: str = None,
        proc_id=None,
    ):

        self.input_label = input_label
        self.output_label = output_label
        if section_dict is None:
            section_dict = self.load_rules(DefaultConfig.section_dict_path)
        self.keyword_processor = KeywordProcessor(case_sensitive=True)
        self.keyword_processor.add_keywords_from_dict(section_dict)
        self.head_before_treat = ["histoire", "evolution"]

        config = dict(
            input_label=input_label,
            output_label=output_label,
            section_dict=section_dict,
        )

        self._description = ProcessingDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )

    def annotate(self, collection: Collection):
        for doc in collection.documents:
            if isinstance(doc, TextDocument):
                self.annotate_document(doc)

    def annotate_document(self, document: TextDocument):
        # Retrieve annotations on which we want to apply section segmentation
        # e.g., raw text
        input_ann_ids = document.segments.get(self.input_label, None)
        if input_ann_ids:
            # only applicable on the complete text (i.e., raw or cleaned text)
            input_ann = document.get_annotation_by_id(input_ann_ids[0])
            sections = self._extract_sections_and_spans(input_ann)
            for section, text, spans in sections:
                output_ann = TextBoundAnnotation(
                    origin_id=self.description.id,
                    label=self.output_label,
                    spans=spans,
                    text=text,
                )
                section_attribute = Attribute(
                    origin_id=self.description.id,
                    label=self.output_label,
                    target_id=output_ann.id,
                    value=section,
                )
                document.add_annotation(output_ann)
                document.add_annotation(section_attribute)

    def _extract_sections_and_spans(self, input_ann: TextBoundAnnotation):
        match = self.keyword_processor.extract_keywords(input_ann.text, span_info=True)
        match = pd.DataFrame(match, columns=["match_type", "start", "end"]).sort_values(
            ["start", "end"]
        )

        match = (
            match.append({"match_type": "head", "start": 0}, ignore_index=True)
            .sort_values("start")
            .assign(
                end=lambda x: x.start.shift(-1)
                .fillna(len(input_ann.text))
                .astype("int")
            )
            .assign(sl=lambda x: x.start - x.end)
            .loc[lambda x: x.sl != 0]
            .drop("sl", axis=1)
            .reset_index(drop=True)
        )

        # set any traitement section occurring before histoire or evolution to traitement entree
        index_before_treat = match.loc[
            lambda x: x.match_type.isin(self.head_before_treat)
        ].index.tolist()
        index_before_treat = min(index_before_treat, default=0)
        match.loc[
            lambda x: (x.match_type == "traitement") & (x.index < index_before_treat),
            "match_type",
        ] = "traitement_entree"

        for index, row in match.iterrows():
            text, spans = span_utils.extract(
                text=input_ann.text,
                spans=input_ann.spans,
                ranges=[(row["start"], row["end"])],
            )
            yield row["match_type"], text, spans

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)

    @staticmethod
    def load_rules(path_to_rules) -> Dict[str, List[str]]:
        """
        Load all rules stored in a yml file

        Parameters
        ----------
        path_to_rules:
            Path to a yml file containing the sections name and their mappings

        Returns
        -------
        Dict[str, List[str]]
            Dictionary where key is the section name and value is the list of all
            equivalent strings.
        """

        with open(path_to_rules, mode="r") as f:
            rules = yaml.safe_load(f)
        return rules
