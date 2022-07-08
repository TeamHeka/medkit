from __future__ import annotations

__all__ = ["NegationDetector", "NegationDetectorRule", "NegationMetadata"]

import dataclasses
import logging
from pathlib import Path
import re
from typing import List, Optional, Union
from typing_extensions import TypedDict

import unidecode
import yaml

from medkit.core import Attribute
from medkit.core.text import ContextOperation, Segment

logger = logging.getLogger(__name__)

_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "negation_detector_default_rules.yml"


@dataclasses.dataclass
class NegationDetectorRule:
    """Regexp-based rule to use with `NegationDetector`

    Input text may be converted before detecting rule.

    Parameters
    ----------
    regexp:
        The regexp pattern used to match a negation
    exclusion_regexps:
        Optional exclusion patterns
    id:
        Unique identifier of the rule to store in the metadata of the entities
    case_sensitive:
        Whether to consider case when running `regexp and `exclusion_regexs`
    unicode_sensitive:
        If True, rule matches are searched on unicode text.
        So, `regexp and `exclusion_regexs` shall not contain non-ASCII chars because
        they would never be matched.
        If False, rule matches are searched on closest ASCII text when possible.
        (cf. NegationDetector)
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


class NegationMetadata(TypedDict):
    """Metadata dict added to negation attributes with `True` value.

    Parameters
    ----------
    rule_id:
        Identifier of the rule used to detect a negation.
        If the rule has no id, then the index of the rule in
        the list of rules is used instead.
    """

    rule_id: Union[str, int]


class NegationDetector(ContextOperation):
    """Annotator creating negation Attributes with True/False values

    Because negation attributes will be attached to whole annotations,
    each input annotation should be "local"-enough rather than
    a big chunk of text (ie a sentence or a syntagma).

    For detecting negation, the module uses rules that may be sensitive to unicode or
    not. When the rule is not sensitive to unicode, we try to convert unicode chars to
    the closest ascii chars. However, some characters need to be pre-processed before
    (e.g., `n°` -> `number`). So, if the text lengths are different, we fall back on
    initial unicode text for detection even if rule is not unicode-sensitive.
    In this case, a warning is logged for recommending to pre-process data.
    """

    def __init__(
        self,
        output_label: str,
        rules: Optional[List[NegationDetectorRule]] = None,
        op_id: Optional[str] = None,
    ):
        """Instantiate the negation detector

        Parameters
        ----------
        output_label:
            The label of the created attributes
        rules:
            The set of rules to use when detecting negation. If none provided,
            the rules in "negation_detector_default_rules.yml" will be used
        op_id:
            Identifier of the detector
        """
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        if rules is None:
            rules = self.load_rules(_PATH_TO_DEFAULT_RULES)

        self._check_rules_sanity(rules)

        self.output_label = output_label
        self.rules = rules

        # pre-compile patterns
        self._non_empty_text_pattern = re.compile(r"[a-z]", flags=re.IGNORECASE)
        self._patterns = [
            re.compile(rule.regexp, flags=0 if rule.case_sensitive else re.IGNORECASE)
            for rule in self.rules
        ]
        self._exclusion_patterns = [
            re.compile(
                "|".join(
                    f"(?:{r})" for r in rule.exclusion_regexps
                ),  # join all exclusions in one pattern
                flags=0 if rule.case_sensitive else re.IGNORECASE,
            )
            if rule.exclusion_regexps
            else None
            for rule in self.rules
        ]
        self._has_non_unicode_sensitive_rule = any(
            not r.unicode_sensitive for r in rules
        )

    def run(self, segments: List[Segment]):
        """Add a negation attribute to each segment with a True/False value.

        Negation attributes with a `True` value have a metadata dict with
        fields described in :class:`.NegationRuleMetadata`.

        Parameters
        ----------
        segments:
            List of segments to detect as being negated or not
        """

        for segment in segments:
            neg_attr = self._detect_negation_in_segment(segment)
            if neg_attr is not None:
                segment.attrs.append(neg_attr)

    def _detect_negation_in_segment(self, segment: Segment) -> Optional[Attribute]:
        # skip empty segment
        if self._non_empty_text_pattern.search(segment.text) is None:
            return None

        text_unicode = segment.text
        text_ascii = None

        if self._has_non_unicode_sensitive_rule:
            # If there exists one rule which is not unicode-sensitive
            text_ascii = unidecode.unidecode(text_unicode)
            # Verify that text length is conserved
            if len(text_ascii) != len(
                text_unicode
            ):  # if text conversion had changed its length
                logger.warning(
                    "Lengths of unicode text and generated ascii text are different. "
                    "Please, pre-process input text before running NegationDetector\n\n"
                    f"Unicode:{text_unicode} (length: {len(text_unicode)})\n"
                    f"Ascii: {text_ascii} (length: {len(text_ascii)})\n"
                )
                # Fallback on unicode text
                text_ascii = text_unicode

        # try all rules until we have a match
        is_negated = False
        for rule_index, rule in enumerate(self.rules):
            pattern = self._patterns[rule_index]
            exclusion_pattern = self._exclusion_patterns[rule_index]
            text = text_unicode if rule.unicode_sensitive else text_ascii
            if pattern.search(text) is not None:
                if exclusion_pattern is None or exclusion_pattern.search(text) is None:
                    is_negated = True
                    break

        if is_negated:
            rule_id = rule.id if rule.id is not None else rule_index
            neg_attr = Attribute(
                label=self.output_label,
                value=True,
                metadata=NegationMetadata(rule_id=rule_id),
            )
        else:
            neg_attr = Attribute(
                label=self.output_label,
                value=False,
            )

        if self._prov_builder is not None:
            self._prov_builder.add_prov(
                neg_attr, self.description, source_data_items=[segment]
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

    @staticmethod
    def _check_rules_sanity(rules: List[NegationDetector]):
        """Check consistency of a set of rules"""

        if any(r.id is not None for r in rules):
            if not all(r.id is not None for r in rules):
                raise ValueError(
                    "Some rules have ids and other do not. Please provide either ids"
                    " for all rules or no ids at all"
                )
            if len(set(r.id for r in rules)) != len(rules):
                raise ValueError(
                    "Some rules have the same id, each rule must have a unique id"
                )
