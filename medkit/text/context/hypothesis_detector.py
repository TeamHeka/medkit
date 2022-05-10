__all__ = ["HypothesisDetector", "HypothesisDetectorRule"]

import dataclasses
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
import unidecode

import yaml

from medkit.core import generate_id, Attribute, OperationDescription, ProvBuilder
from medkit.core.text import Segment


_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "hypothesis_detector_default_rules.yml"
_PATH_TO_DEFAULT_VERBS = Path(__file__).parent / "hypothesis_detector_default_verbs.yml"


@dataclasses.dataclass
class HypothesisDetectorRule:
    """Regexp-based rule to use with `HypothesisDetector`

    Attributes
    ----------
    regexp:
        The regexp pattern used to match a hypothesis
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
            "HypothesisDetectorRule regexps shouldn't contain non-ASCII chars when"
            " unicode_sensitive is False"
        )


class HypothesisDetector:
    """Annotator creating hypothesis Attributes with True/False values

    Hypothesis will be considered present either because of the presence of a
    certain text pattern in a segment, or because of the usage of a certain verb
    at a specific mode and tense (for instance conditional).

    Because hypothesis attributes will be attached to whole segments,
    each input segment should be "local"-enough (ie a sentence or a syntagma)
    rather than a big chunk of text.
    """

    def __init__(
        self,
        output_label: str = "hypothesis",
        rules: Optional[List[HypothesisDetectorRule]] = None,
        verbs: Optional[Dict[str, Dict[str, Dict[str, List[str]]]]] = None,
        modes_and_tenses: Optional[List[Tuple[str, str]]] = None,
        proc_id: Optional[str] = None,
    ):
        """Instantiate the hypothesis detector

        Parameters
        ----------
        output_label:
            The label of the created attributes
        rules:
            The set of rules to use when detecting hypothesis. If none provided,
            the rules in "hypothesis_detector_default_rules.yml" will be used
        verbs:
            Conjugated verbs forms, to be used in association with `modes_and_tenses`.
            Conjugated forms of a verb at a specific mode and tense must be provided
            in nested dicts with the 1st key being the verb's root, the 2d key the mode
            and the 3d key the tense.
            For instance verb["aller"]["indicatif]["présent"] would hold the list
            ["vais", "vas", "va", "allons", aller", "vont"]
        modes_and_tenses:
            List of tuples of all modes and tenses associated with hypothesis.
            Will be used to select conjugated forms in `verbs` that denote hypothesis.
        proc_id:
            Identifier of the detector
        """
        if proc_id is None:
            proc_id = generate_id()
        if rules is None:
            rules = self.load_rules(_PATH_TO_DEFAULT_RULES)
        if verbs is None:
            verbs = self.load_verbs(_PATH_TO_DEFAULT_VERBS)
        if modes_and_tenses is None:
            modes_and_tenses = [
                ("conditionnel", "présent"),
                ("indicatif", "futur simple"),
            ]

        self.id: str = proc_id
        self.output_label: str = output_label
        self.rules: List[HypothesisDetectorRule] = rules
        self.verbs: Dict[str, Dict[str, Dict[str, List[str]]]] = verbs
        self.modes_and_tenses: List[Tuple[str, str]] = modes_and_tenses

        # build and pre-compile exclusion pattern for each verb
        self._patterns_by_verb = {}
        for verb_root, verb_forms_by_mode_and_tense in verbs.items():
            verb_regexps = []
            for mode, tense in modes_and_tenses:
                for verb_form in verb_forms_by_mode_and_tense[mode][tense]:
                    verb_regexp = r"\b" + verb_form.replace(" ", r"\s+") + r"\b"
                    verb_regexps.append(verb_regexp)
            verb_pattern = re.compile("|".join(verb_regexps), flags=re.IGNORECASE)
            self._patterns_by_verb[verb_root] = verb_pattern

        # pre-compile rule patterns
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

        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        config = dict(
            output_label=self.output_label,
            rules=self.rules,
            verbs=self.verbs,
            modes_and_tenses=self.modes_and_tenses,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def run(self, segments: List[Segment]):
        """Add an hypothesis attribute to each segment with a True/False value

        Parameters
        ----------
        segments:
            List of segments to detect as being hypothesis or not
        """

        for segment in segments:
            hyp_attr = self._detect_hypothesis_in_segment(segment)
            segment.attrs.append(hyp_attr)

    def _detect_hypothesis_in_segment(self, segment: Segment) -> Attribute:
        is_hypothesis = False
        metadata = None

        if len(segment.text) <= 150:
            text_unicode = segment.text
            if self._has_non_unicode_sensitive_rule:
                # If there exists one rule which is not unicode-sensitive
                text_ascii = unidecode.unidecode(text_unicode)
                # Verify that text length is conserved
                if len(text_ascii) != len(
                    text_unicode
                ):  # if text conversion had changed its length
                    raise ValueError(
                        "Lengths of unicode text and generated ascii text are"
                        " different. Please, pre-process input text before running"
                        f" RegexpMatcher\n\nUnicode:{text_unicode} (length:"
                        f" {len(text_unicode)})\nAscii: {text_ascii} (length:"
                        f" {len(text_ascii)})\n"
                    )
            for verb, verb_pattern in self._patterns_by_verb.items():
                if verb_pattern.search(text_unicode):
                    metadata = dict(matched_verb=verb)
                    is_hypothesis = True
                    break
            else:
                for rule in self.rules:
                    text = text_unicode if rule.unicode_sensitive else text_ascii
                    pattern = self._patterns_by_rule_id[rule.id]
                    if pattern.search(text) is not None:
                        exclusion_pattern = self._exclusion_patterns_by_rule_id.get(
                            rule.id
                        )
                        if (
                            exclusion_pattern is None
                            or exclusion_pattern.search(text) is None
                        ):
                            is_hypothesis = True
                            if rule.id is not None:
                                metadata = dict(rule_id=rule.id)
                            break

        hyp_attr = Attribute(
            label=self.output_label, value=is_hypothesis, metadata=metadata,
        )

        if self._prov_builder is not None:
            self._prov_builder.add_prov(
                hyp_attr, self.description, source_data_items=[segment]
            )

        return hyp_attr

    @staticmethod
    def load_verbs(path_to_verbs) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        """
        Load all conjugated verb forms stored in a yml file.
        Conjugated verb forms at a specific mode and tense must be stored in nested mappings
        with the 1st key being the verb root, the 2d key the mode and the 3d key the tense.

        Parameters
        ----------
        path_to_verbs:
            Path to a yml file containing a list of verbs form,
            arranged by mode and tense.

        Returns
        -------
        List[Dict[str, Dict[str, List[str]]]]
            List of verb forms in `path_to_verbs`,
            can be used to init an `HypothesisDetector`
        """
        with open(path_to_verbs) as f:
            verbs = yaml.safe_load(f)
        return verbs

    @staticmethod
    def load_rules(path_to_rules) -> List[HypothesisDetectorRule]:
        """
        Load all rules stored in a yml file

        Parameters
        ----------
        path_to_rules:
            Path to a yml file containing a list of mappings
            with the same structure as `HypothesisDetectorRule`

        Returns
        -------
        List[HypothesisDetectorRule]
            List of all the rules in `path_to_rules`,
            can be used to init an `HypothesisDetector`
        """

        with open(path_to_rules, mode="r") as f:
            rules_data = yaml.safe_load(f)
        rules = [HypothesisDetectorRule(**d) for d in rules_data]
        return rules
