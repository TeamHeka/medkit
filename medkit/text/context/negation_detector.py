__all__ = ["NegationDetector", "NegationDetectorRule"]

import dataclasses
from pathlib import Path
import re
from typing import List, Optional

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
    """

    regexp: str
    exclusion_regexps: List[str] = dataclasses.field(default_factory=lambda: [])
    id: Optional[str] = None


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
            # skip empty annotations
            if re.search(r"[a-z]", segment.text, flags=re.IGNORECASE) is None:
                continue

            is_negated = False
            # try all rules until we have a match
            for rule in self.rules:
                is_negated = re.search(
                    rule.regexp, segment.text, flags=re.IGNORECASE
                ) is not None and all(
                    re.search(p, segment.text, flags=re.IGNORECASE) is None
                    for p in rule.exclusion_regexps
                )
                if is_negated:
                    break

            attr = Attribute(
                origin=Origin(
                    operation_id=self.description.id,
                    ann_ids=[segment.id],
                ),
                label=self.output_label,
                value=is_negated,
                metadata=dict(rule_id=rule.id) if is_negated else None,
            )
            segment.attrs.append(attr)

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
