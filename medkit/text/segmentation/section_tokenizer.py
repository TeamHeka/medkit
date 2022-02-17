from __future__ import annotations

__all__ = ["SectionTokenizer"]

import dataclasses
import pathlib
import pandas as pd
import yaml
from flashtext import KeywordProcessor
from typing import Dict, List, Literal, Tuple

from medkit.core.document import Collection
from medkit.core.processing import ProcessingDescription
from medkit.core.text import Attribute, TextBoundAnnotation, TextDocument
from medkit.core.text import span as span_utils


@dataclasses.dataclass
class SectionModificationRule:
    section_name: str
    new_section_name: str
    other_sections: List[str]
    order: Literal["BEFORE", "AFTER"]


class SectionTokenizer:
    """Section segmentation annotator based on keyword rules"""

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def __init__(
        self,
        section_dict: Dict[str, List[str]],
        input_label: str = "CLEAN_TEXT",
        output_label: str = "SECTION",
        section_rules: List[SectionModificationRule] = None,
        proc_id: str = None,
    ):
        """
        Initialize the Section Tokenizer

        Parameters
        ----------
        section_dict
            Dictionary containing the section name as key and the list of mappings
            as value (cf. content of default_section_dict.yml as example)
        input_label
            Segment label to use as input. Default is CLEAN_TEXT.
        output_label
            Segment label to use for annotation output. Default is SECTION.
        section_rules
            List of rules for modifying a section name according its order to the other
            sections.
        """

        self.input_label = input_label
        self.output_label = output_label
        self.section_dict = section_dict
        self.section_rules = section_rules
        self.keyword_processor = KeywordProcessor(case_sensitive=True)
        self.keyword_processor.add_keywords_from_dict(section_dict)

        config = dict(
            input_label=input_label,
            output_label=output_label,
            section_dict=section_dict,
            section_rules=section_rules,
        )

        self._description = ProcessingDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )

    def annotate(self, collection: Collection):
        """Annotate a collection of documents"""
        for doc in collection.documents:
            if isinstance(doc, TextDocument):
                self.annotate_document(doc)

    def annotate_document(self, document: TextDocument):
        """Annotate a document"""
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
        # Process mappings
        match = self.keyword_processor.extract_keywords(input_ann.text, span_info=True)
        match = pd.DataFrame(match, columns=["match_type", "start", "end"]).sort_values(
            ["start", "end"]
        )
        # Fill dataframe to include all input annotation text
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

        # Rename some sections according defined rules
        # e.g., set any 'traitement' section occurring before 'histoire' or 'evolution'
        # to 'traitement entree' (cf. example)
        match = self._rename_sections(match)

        # Extract medkit spans from relative spans (i.e., ranges)
        for index, row in match.iterrows():
            text, spans = span_utils.extract(
                text=input_ann.text,
                spans=input_ann.spans,
                ranges=[(row["start"], row["end"])],
            )
            yield row["match_type"], text, spans

    def _rename_sections(self, match: pd.DataFrame):
        for rule in self.section_rules:
            name = rule.section_name
            new_name = rule.new_section_name
            index_other_sections = match.loc[
                lambda x: x.match_type.isin(rule.other_sections)
            ].index.tolist()

            if rule.order == "BEFORE":
                # Change section name if section is before one of the listed sections
                index_other_sections = max(index_other_sections, default=0)
                match.loc[
                    lambda x: (x.match_type == name) & (x.index < index_other_sections),
                    "match_type",
                ] = new_name
            elif rule.order == "AFTER":
                # Change section name if the section is after one of the listed sections
                index_other_sections = min(
                    index_other_sections, default=max(match.index)
                )
                match.loc[
                    lambda x: (x.match_type == name) & (x.index > index_other_sections),
                    "match_type",
                ] = new_name

        return match

    @classmethod
    def get_example(cls):
        config_path = pathlib.Path(__file__).parent / "default_section_dict.yml"
        section_dict, section_rules = cls.load_config(config_path)
        section_tokenizer = cls(
            section_dict=section_dict,
            section_rules=section_rules,
        )
        return section_tokenizer

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)

    @staticmethod
    def load_config(
        path_to_config,
    ) -> Tuple[Dict[str, List[str]], List[SectionModificationRule]]:
        """
        Load the config stored in a yml file

        Parameters
        ----------
        path_to_config:
            Path to a yml file containing the sections(name + mappings) and rules

        Returns
        -------
        Dict[str, List[str]]
            Dictionary where key is the section name and value is the list of all
            equivalent strings.
        """

        with open(path_to_config, mode="r") as f:
            config = yaml.safe_load(f)

        section_dict = config.get("sections")
        section_rules = [
            SectionModificationRule(**rule) for rule in config.get("rules")
        ]

        return section_dict, section_rules
