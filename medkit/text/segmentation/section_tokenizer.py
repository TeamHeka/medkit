from __future__ import annotations

__all__ = ["SectionModificationRule", "SectionTokenizer"]

import dataclasses
import pathlib
from typing import Dict, List, Optional, Tuple
from typing_extensions import Literal
import yaml

from flashtext import KeywordProcessor

from medkit.core.text import Segment, SegmentationOperation, span_utils


_DEFAULT_SECTION_DEFINITION_RULES = (
    pathlib.Path(__file__).parent / "default_section_definition.yml"
)


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    output_label: str = "SECTION"


@dataclasses.dataclass
class SectionModificationRule:
    section_name: str
    new_section_name: str
    other_sections: List[str]
    order: Literal["BEFORE", "AFTER"]


class SectionTokenizer(SegmentationOperation):
    """Section segmentation annotator based on keyword rules"""

    def __init__(
        self,
        section_dict: Dict[str, List[str]],
        output_label: str = DefaultConfig.output_label,
        section_rules: Tuple[SectionModificationRule] = (),
        uid: Optional[str] = None,
    ):
        """
        Initialize the Section Tokenizer

        Parameters
        ----------
        section_dict
            Dictionary containing the section name as key and the list of mappings
            as value (cf. content of default_section_dict.yml as example)
        output_label
            Segment label to use for annotation output. Default is SECTION.
        section_rules
            List of rules for modifying a section name according its order to the other
            sections.
        """
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        self.output_label = output_label
        self.section_dict = section_dict
        self.section_rules = section_rules
        self.keyword_processor = KeywordProcessor(case_sensitive=True)
        self.keyword_processor.add_keywords_from_dict(section_dict)

    def run(self, segments: List[Segment]) -> List[Segment]:
        """
        Return sections detected in `segments`.

        Parameters
        ----------
        segments:
            List of segments into which to look for sections

        Returns
        -------
        List[Segments]:
            Sections segments found in `segments`
        """
        return [
            section
            for segment in segments
            for section in self._find_sections_in_segment(segment)
        ]

    def _find_sections_in_segment(self, segment: Segment):
        # Process mappings
        match = self.keyword_processor.extract_keywords(segment.text, span_info=True)

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
                ranges = [(section[1], match[index + 1][1])]
            else:
                ranges = [(section[1], len(segment.text))]

            # Extract medkit spans from relative spans (i.e., ranges)
            text, spans = span_utils.extract(
                text=segment.text,
                spans=segment.spans,
                ranges=ranges,
            )

            # add section name in metadata
            metadata = dict(name=name)
            section = Segment(
                label=self.output_label,
                spans=spans,
                text=text,
                metadata=metadata,
            )

            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    section, self.description, source_data_items=[segment]
                )

            yield section

    def _get_sections_to_rename(self, match: List[Tuple]):
        match_type = [m[0] for m in match]
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
        config_path = _DEFAULT_SECTION_DEFINITION_RULES
        section_dict, section_rules = cls.load_section_definition(
            config_path, encoding="utf-8"
        )
        section_tokenizer = cls(
            section_dict=section_dict,
            section_rules=section_rules,
        )
        return section_tokenizer

    @staticmethod
    def load_section_definition(
        filepath: pathlib.Path, encoding: Optional[str] = None
    ) -> Tuple[Dict[str, List[str]], Tuple[SectionModificationRule]]:
        """
        Load the sections definition stored in a yml file

        Parameters
        ----------
        filepath:
            Path to a yml file containing the sections(name + mappings) and rules
        encoding:
            Encoding of the file to open

        Returns
        -------
        Tuple[Dict[str, List[str]], Tuple[SectionModificationRule]]
            Tuple containing:
            - the dictionary where key is the section name and value is the list of all
            equivalent strings.
            - the list of section modification rules.
            These rules allow to rename some sections according their order
        """

        with open(filepath, mode="r", encoding=encoding) as f:
            config = yaml.safe_load(f)

        section_dict = config["sections"]
        section_rules = tuple(
            SectionModificationRule(**rule) for rule in config["rules"]
        )

        return section_dict, section_rules
