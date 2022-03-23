from __future__ import annotations

__all__ = ["RegexpMatcher", "RegexpMatcherRule", "RegexpMatcherNormalization"]

import dataclasses
from pathlib import Path
import re
from typing import Any, Iterator, List, Optional

import unidecode
import yaml


from medkit.core import (
    Attribute,
    OperationDescription,
    RuleBasedAnnotator,
    ProvBuilder,
    generate_id,
)
from medkit.core.text import Entity, Segment, span_utils


@dataclasses.dataclass
class RegexpMatcherRule:
    """
    Regexp-based rule to use with `RegexpMatcher`

    Attributes
    ----------
    regexp:
        The regexp pattern used to match entities
    label:
        The label to attribute to entities created based on this rule
    id:
        Unique identifier of the rule to store in the metadata of the entities
    version:
        Version string to store in the metadata of the entities
    index_extract:
        If the regexp has groups, the index of the group to use to extract
        the entity
    case_sensitive:
        Wether to ignore case when running `regexp and `exclusion_regexp`
    exclusion_regexp:
        An optional exclusion pattern. Note that this exclusion pattern will
        executed on the whole input annotation, so when relying on `exclusion_regexp`
        make sure the input annotations passed to `RegexpMatcher` are "local"-enough
        (sentences or syntagmes) rather than the whole text or paragraphs
    normalization:
        Optional list of normalization attributes that should be attached to
        the entities created
    """

    regexp: str
    label: str
    id: str
    version: str
    index_extract: int = 0
    case_sensitive: bool = False
    unicode_sensitive: bool = False
    exclusion_regexp: Optional[str] = None
    normalizations: List[RegexpMatcherNormalization] = dataclasses.field(
        default_factory=list
    )

    def __post_init__(self):
        assert self.unicode_sensitive or (
            self.regexp.isascii()
            and (self.exclusion_regexp is None or self.exclusion_regexp.isascii())
        ), (
            "NegationDetectorRule regexps shouldn't contain non-ASCII chars when"
            " unicode_sensitive is False"
        )


@dataclasses.dataclass
class RegexpMatcherNormalization:
    """
    Descriptor of normalization attributes to attach to entities
    created from a `RegexpMatcherRule`

    Attributes
    ----------
    kb_name:
        The name of the knowledge base we are referencing. Ex: "umls"
    kb_version:
        The name of the knowledge base we are referencing. Ex: "202AB"
    id:
        The id of the entity in the knowledge base, for instance a CUI
    """

    kb_name: str
    kb_version: str
    id: Any


_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "regexp_matcher_default_rules.yml"


class RegexpMatcher(RuleBasedAnnotator):
    """Entity annotator relying on regexp-based rules"""

    def __init__(
        self,
        rules: Optional[List[RegexpMatcherRule]] = None,
        attrs_to_copy: Optional[List[str]] = None,
        proc_id: Optional[str] = None,
    ):
        """
        Instantiate the regexp matcher

        Parameters
        ----------
        rules:
            The set of rules to use when matching entities. If none provided,
            the rules in "regexp_matcher_default_rules.yml" will be used
        attrs_to_copy:
            Labels of the attributes that should be copied from the source segment
            to the created entity. Useful for propagating context attributes
            (negation, antecendent, etc)
        proc_id:
            Identifier of the tokenizer
        """
        if proc_id is None:
            proc_id = generate_id()
        if rules is None:
            rules = self.load_rules(_PATH_TO_DEFAULT_RULES)
        if attrs_to_copy is None:
            attrs_to_copy = []

        assert len(set(r.id for r in rules)) == len(rules), "Rule have duplicate ids"

        self.id: str = proc_id
        self.rules = rules
        self.attrs_to_copy = attrs_to_copy

        # pre-compile patterns
        self._patterns_by_rule_id = {
            rule.id: re.compile(
                rule.regexp, flags=0 if rule.case_sensitive else re.IGNORECASE
            )
            for rule in self.rules
        }
        self._exclusion_patterns_by_rule_id = {
            rule.id: re.compile(
                rule.exclusion_regexp, flags=0 if rule.case_sensitive else re.IGNORECASE
            )
            for rule in self.rules
            if rule.exclusion_regexp is not None
        }
        self._has_non_unicode_sensitive_rule = any(
            not r.unicode_sensitive for r in rules
        )

        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        config = dict(rules=self.rules, attrs_to_copy=self.attrs_to_copy)
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def process(self, segments: List[Segment]) -> List[Entity]:
        """
        Return entities (with optional normalization attributes) matched in `segments`

        Parameters
        ----------
        segments:
            List of segments into which to look for matches

        Returns
        -------
        entities: List[Entity]:
            Entities found in `segments` (with optional normalization attributes)
        """
        return [
            entity
            for segment in segments
            for entity in self._find_matches_in_segment(segment)
        ]

    def _find_matches_in_segment(self, segment: Segment) -> Iterator[Entity]:
        text_ascii = (
            unidecode.unidecode(segment.text)
            if self._has_non_unicode_sensitive_rule
            else None
        )

        for rule in self.rules:
            yield from self._find_matches_in_segment_for_rule(rule, segment, text_ascii)

    def _find_matches_in_segment_for_rule(
        self, rule: RegexpMatcherRule, segment: Segment, text_ascii: Optional[str]
    ) -> Iterator[Entity]:
        flags = 0 if rule.case_sensitive else re.IGNORECASE
        text_to_match = segment.text if rule.unicode_sensitive else text_ascii

        pattern = self._patterns_by_rule_id[rule.id]
        for match in pattern.finditer(text_to_match, flags):
            # note that we apply exclusion_regexp to the whole segment,
            # so we might have a match in a part of the text unrelated to the current
            # match
            # we could check if we have any exclude match overlapping with
            # the current match but that wouldn't work for all cases
            exclusion_pattern = self._exclusion_patterns_by_rule_id.get(rule.id)
            if (
                exclusion_pattern is not None
                and exclusion_pattern.search(text_to_match, flags) is not None
            ):
                continue

            # extract raw span list from regex match range
            text, spans = span_utils.extract(
                segment.text, segment.spans, [match.span(rule.index_extract)]
            )

            metadata = dict(
                rule_id=rule.id,
                version=rule.version,
            )

            attrs = [a for a in segment.attrs if a.label in self.attrs_to_copy]

            # create normalization attributes for each normalization descriptor
            # of the rule
            # TODO should we have a NormalizationAttribute class
            # with specific fields (name, id, version) ?

            norm_attrs = [
                Attribute(
                    label=norm.kb_name,
                    value=norm.id,
                    metadata=dict(version=norm.kb_version),
                )
                for norm in rule.normalizations
            ]
            attrs += norm_attrs

            entity = Entity(
                label=rule.label,
                text=text,
                spans=spans,
                attrs=attrs,
                metadata=metadata,
            )

            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    entity, self.description, source_data_items=[segment]
                )
                for norm_attr in norm_attrs:
                    self._prov_builder.add_prov(
                        norm_attr, self.description, source_data_items=[segment]
                    )

            yield entity

    @classmethod
    def from_description(cls, description: OperationDescription):
        return cls(proc_id=description.id, **description.config)

    @staticmethod
    def load_rules(path_to_rules) -> List[RegexpMatcherRule]:
        """
        Load all rules stored in a yml file

        Parameters
        ----------
        path_to_rules:
            Path to a yml file containing a list of mappings
            with the same structure as `RegexpMatcherRule`

        Returns
        -------
        List[RegexpMatcherRule]
            List of all the rules in `path_to_rules`,
            can be used to init a `RegexpMatcher`
        """

        class Loader(yaml.Loader):
            pass

        def construct_mapping(loader, node):
            data = loader.construct_mapping(node)
            if "kb_name" in data:
                return RegexpMatcherNormalization(**data)
            else:
                return RegexpMatcherRule(**data)

        Loader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )

        with open(path_to_rules, mode="r") as f:
            rules = yaml.load(f, Loader=Loader)
        return rules
