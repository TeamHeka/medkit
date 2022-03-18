__all__ = ["NegationDetector", "NegationDetectorRule"]

import dataclasses
from pathlib import Path
import re
from typing import List, Optional

import unidecode
import yaml

from medkit.core import Origin, Attribute, OperationDescription, RuleBasedAnnotator
from medkit.core.text import Segment


_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "negation_detector_default_rules.yml"


@dataclasses.dataclass
class NegationDetectorRule:
    """Regexp-based rule to use with `NegationDetector`

    Attributes
    ----------
    regexp:
        The regexp pattern used to match a negation
    exclusion_regexps:
        Optional exclusion patterns
    id:
        Unique identifier of the rule to store in the metadata of the entities
    case_sensitive:
        Wether to ignore case when running `regexp and `exclusion_regexs`
    unicode_sensitive:
        Wether to replace all non-ASCII chars by the closest ASCII chars
        on input text before runing `regexp and `exclusion_regexs`.
        If True, then `regexp and `exclusion_regexs` shouldn't contain
        non-ASCII chars because they would never be matched.
    """

    regexp: str
    exclusion_regexps: List[str] = dataclasses.field(default_factory=list)
    id: Optional[str] = None
    case_sensitive: bool = False
    unicode_sensitive: bool = False

    def __post_init__(self):
        assert self.unicode_sensitive or (
            self.regexp.isascii() and all(r.isascii() for r in self.exclusion_regexps)
        ), (
            "NegationDetectorRule regexps shouldn't contain non-ASCII chars when"
            " unicode_sensitive is False"
        )


class NegationDetector(RuleBasedAnnotator):
    """Annotator creating negation Attributes with True/False values

    Because negation attributes will be attached to whole annotations,
    each input annotation should be "local"-enough rather than
    a big chunk of text (ie a sentence or a syntagma).
    """

    def __init__(
        self,
        output_label: str,
        rules: Optional[List[NegationDetectorRule]] = None,
        proc_id: Optional[str] = None,
    ):
        """Instantiate the negation detector

        Parameters
        ----------
        output_label:
            The output label of the created annotations
        rules:
            The set of rules to use when detecting negation. If none provided,
            the rules in "negation_detector_default_rules.yml" will be used
        proc_id:
            Identifier of the detector
        """
        self.output_label = output_label

        if rules is None:
            rules = self.load_rules(_PATH_TO_DEFAULT_RULES)
        assert len(set(r.id for r in rules)) == len(rules), "Rule have duplicate ids"
        self.rules = rules

        # pre-compile patterns
        self._non_empty_text_pattern = re.compile(r"[a-z]", flags=re.IGNORECASE)
        self._patterns_by_rule_id = {
            rule.id: re.compile(
                rule.regexp, flags=0 if rule.case_sensitive else re.IGNORECASE
            )
            for rule in self.rules
        }
        self._exclusion_patterns_by_rule_id = {
            rule.id: re.compile(
                "|".join(
                    f"(?:{r})" for r in rule.exclusion_regexps
                ),  # join all exclusions in one pattern
                flags=0 if rule.case_sensitive else re.IGNORECASE,
            )
            for rule in self.rules
            if rule.exclusion_regexps
        }
        self._has_non_unicode_sensitive_rule = any(
            not r.unicode_sensitive for r in rules
        )

        config = dict(output_label=output_label, rules=rules)
        self._description = OperationDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )

    @property
    def description(self) -> OperationDescription:
        return self._description

    def process(self, segments: List[Segment]):
        """Add a negation attribute to each segment with a True/False value.

        Parameters
        ----------
        segments:
            List of segments to detect as being negated or not
        """

        for segment in segments:
            neg_attr = self._detect_negation_in_segment(segment)
            segment.attrs.append(neg_attr)

    def _detect_negation_in_segment(self, segment: Segment):
        # skip empty segment
        if self._non_empty_text_pattern.search(segment.text) is None:
            return

        text_unicode = segment.text
        text_ascii = (
            unidecode.unidecode(text_unicode)
            if self._has_non_unicode_sensitive_rule
            else None
        )

        # try all rules until we have a match
        is_negated = False
        for rule in self.rules:
            text = text_unicode if rule.unicode_sensitive else text_ascii
            pattern = self._patterns_by_rule_id[rule.id]
            if pattern.search(text) is not None:
                exclusion_pattern = self._exclusion_patterns_by_rule_id.get(rule.id)
                if exclusion_pattern is None or exclusion_pattern.search(text) is None:
                    is_negated = True
                    break

        neg_attr = Attribute(
            origin=Origin(
                operation_id=self.description.id,
                ann_ids=[segment.id],
            ),
            label=self.output_label,
            value=is_negated,
            metadata=dict(rule_id=rule.id) if is_negated else None,
        )
        return neg_attr

    @staticmethod
    def load_rules(path_to_rules) -> List[NegationDetectorRule]:
        """
        Load all rules stored in a yml file

        Parameters
        ----------
        path_to_rules:
            Path to a yml file containing a list of mappings
            with the same structure as `NegationDetectorRule`

        Returns
        -------
        List[NegationDetectorRule]
            List of all the rules in `path_to_rules`,
            can be used to init a `NegationDetector`
        """

        with open(path_to_rules, mode="r") as f:
            rules_data = yaml.safe_load(f)
        rules = [NegationDetectorRule(**d) for d in rules_data]
        return rules
