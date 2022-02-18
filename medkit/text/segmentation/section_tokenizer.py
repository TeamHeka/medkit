from __future__ import annotations

__all__ = ["SectionModificationRule", "SectionTokenizer"]

import dataclasses
import pathlib
import yaml

from flashtext import KeywordProcessor
from typing import Dict, Generator, List, Literal, Tuple

from medkit.core import Collection, Origin
from medkit.core.processing import ProcessingDescription
from medkit.core.text import TextBoundAnnotation, TextDocument
from medkit.core.text import span as span_utils


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    input_label: str = "CLEAN_TEXT"
    output_label: str = "SECTION"


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
        input_label: str = DefaultConfig.input_label,
        output_label: str = DefaultConfig.output_label,
        section_rules: Tuple[SectionModificationRule] = (),
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
                # add section name in metadata
                metadata = dict(name=section)
                output_ann = TextBoundAnnotation(
                    origin=Origin(
                        processing_id=self.description.id, ann_ids=[input_ann.id]
                    ),
                    label=self.output_label,
                    spans=spans,
                    text=text,
                    metadata=metadata,
                )
                document.add_annotation(output_ann)

    def _extract_sections_and_spans(self, input_ann: TextBoundAnnotation):
        # Process mappings
        match = self.keyword_processor.extract_keywords(input_ann.text, span_info=True)

        # Sort according to the match start
        match.sort(key=lambda x: x[1])
        if len(match) == 0 or match[0][1] != 0:
            # Add head before any detected sections
            match.insert(0, ("head", 0, 0))

        # Get sections to rename according defined rules
        # e.g., set any 'traitement' section occurring before 'histoire' or 'evolution'
        # to 'traitement entree' (cf. example)
        new_sections = self._get_sections_to_rename(match)

        for index, section in enumerate(match):
            name = new_sections.get(index, section[0])
            if index != len(match) - 1:
                ranges = [(section[1], match[index+1][1])]
            else:
                ranges = [(section[1], len(input_ann.text))]

            # Extract medkit spans from relative spans (i.e., ranges)
            text, spans = span_utils.extract(
                text=input_ann.text,
                spans=input_ann.spans,
                ranges=ranges,
            )
            yield name, text, spans

    def _get_sections_to_rename(self, match: List[Tuple]):
        match_type = list(zip(*zip(match)))[0]
        map_index_new_name = {}
        list_to_process = ()
        for rule in self.section_rules:
            if rule.order == "BEFORE":
                # Change section name if section is before one of the listed sections
                list_to_process = enumerate(match_type)
            elif rule.order == "AFTER":
                # Change section name if the section is after one of the listed sections
                list_to_process = reversed(list(enumerate(match_type)))

            # Navigate in list according to the order defined above
            candidate_sections = []
            for index, section_name in list_to_process:
                if section_name == rule.section_name:
                    candidate_sections.append(index)
                if section_name in rule.other_sections:
                    for candidate_index in candidate_sections:
                        map_index_new_name[candidate_index] = rule.new_section_name
                    candidate_sections.clear()

        return map_index_new_name

    @classmethod
    def get_example(cls):
        config_path = pathlib.Path(__file__).parent / "default_section_definition.yml"
        section_dict, section_rules = cls.load_section_definition(config_path)
        section_tokenizer = cls(
            section_dict=section_dict,
            section_rules=section_rules,
        )
        return section_tokenizer

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)

    @staticmethod
    def load_section_definition(
        filepath,
    ) -> Tuple[Dict[str, List[str]], Generator[SectionModificationRule]]:
        """
        Load the sections definition stored in a yml file

        Parameters
        ----------
        filepath:
            Path to a yml file containing the sections(name + mappings) and rules

        Returns
        -------
        Tuple[Dict[str, List[str]], Generator[SectionModificationRule]]
            Tuple containing:
            - the dictionary where key is the section name and value is the list of all
            equivalent strings.
            - the list of section modification rules.
            These rules allow to rename some sections according their order
        """

        with open(filepath, mode="r") as f:
            config = yaml.safe_load(f)

        section_dict = config["sections"]
        section_rules = (SectionModificationRule(**rule) for rule in config["rules"])

        return section_dict, section_rules
