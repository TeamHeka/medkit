__all__ = ["HypothesisDetector"]

from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

import yaml

from medkit.core import generate_id, Attribute
from medkit.core.text import Segment


_PATH_TO_DEFAULT_VERBS = Path(__file__).parent / "hypothesis_detector_default_verbs.yml"


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
        verbs: Optional[List[Dict[str, Dict[str, List[str]]]]] = None,
        modes_and_tenses: Optional[List[Tuple[str, str]]] = None,
        proc_id: Optional[str] = None,
    ):
        """Instantiate the hypothesis detector

        Parameters
        ----------
        output_label:
            The label of the created attributes
        verbs:
            List of conjugated verbs forms, to be used in association with `modes_and_tenses`
            Each verb must be represent by a dict with an entry for each mode,
            and for each mode an entry for each tense holding a list of the
            conjugated forms.
        modes_and_tenses:
            List of tuples of all modes and tenses associated with hypothesis.
            Will be used to select conjugated forms in `verbs` that denote hypothesis.
        proc_id:
            Identifier of the detector
        """
        if proc_id is None:
            proc_id = generate_id()
        if verbs is None:
            verbs = self.load_verbs(_PATH_TO_DEFAULT_VERBS)
        if modes_and_tenses is None:
            modes_and_tenses = [
                ("conditionnel", "présent"),
                ("indicatif", "futur simple"),
            ]

        self.id: str = proc_id
        self.output_label: str = output_label
        self.verbs: List[Dict[str, Dict[str, List[str]]]] = verbs
        self.modes_and_tenses: List[Tuple[str, str]] = modes_and_tenses

        # build and pre-compile exclusion pattern for each verb
        self._verb_patterns = []
        for verb_form_by_mode_and_tense in verbs:
            verb_regexps = []
            for mode, tense in modes_and_tenses:
                for verb_form in verb_form_by_mode_and_tense[mode][tense]:
                    verb_regexp = r"\b" + verb_form.replace(" ", r"\s+") + r"\b"
                    verb_regexps.append(verb_regexp)
            verb_pattern = re.compile("|".join(verb_regexps), flags=re.IGNORECASE)
            self._verb_patterns.append(verb_pattern)

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
        phrase = segment.text
        if len(phrase) > 150:
            is_hypothesis = False
        else:
            phrase_low = phrase.lower()
            for verb_pattern in self._verb_patterns:
                if verb_pattern.search(phrase_low):
                    is_hypothesis = True
                    break
            else:
                if (
                    (
                        (re.findall(r"\bsi\b", phrase_low) != [])
                        & (re.findall(r"\bsi\s+oui\b", phrase_low) == [])
                        & (re.findall(r"\bm[eê]me\s+si\b", phrase_low) == [])
                    )
                    | (re.findall(r"\b[àa]\s+condition\s+que\b", phrase_low) != [])
                    | (re.findall(r"\b[àa]\s+moins\s+que\b", phrase_low) != [])
                    | (re.findall(r"\bpour\s+peu\s+que\b", phrase_low) != [])
                    | (re.findall(r"\bsi\s+tant\s+est\s+que\b", phrase_low) != [])
                    | (re.findall(r"\bpour\s+autant\s+que\b", phrase_low) != [])
                    | (re.findall(r"\ben\s+admettant\s+que\b", phrase_low) != [])
                    | (re.findall(r"\b[àa]\s+supposer\s+que\b", phrase_low) != [])
                    | (re.findall(r"\ben\s+supposant\s+que\b", phrase_low) != [])
                    | (re.findall(r"\bau\s+cas\s+o[uù]\b", phrase_low) != [])
                    | (re.findall(r"\b[ée]ventuellement\b", phrase_low) != [])
                    | (re.findall(r"\bsuspicion\b", phrase_low) != [])
                    | (
                        (re.findall(r"\bsuspect[ée]e?s?\b", phrase_low) != [])
                        & (re.findall(r"\bconfirm[ée]e?s?\b", phrase_low) == [])
                    )
                    | (re.findall(r"\benvisag[eé]e?s?r?\b", phrase_low) != [])
                ):

                    is_hypothesis = True
                else:
                    is_hypothesis = False

        hyp_attr = Attribute(label=self.output_label, value=is_hypothesis,)
        return hyp_attr

    @staticmethod
    def load_verbs(path_to_verbs) -> List[Dict[str, Dict[str, List[str]]]]:
        """
        Load all conjugated verb forms stored in a yml file.
        Each verb must be represented by a mapping with an entry for each mode,
        and for each mode an entry for each tense holding a list of the
        conjugated forms.

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
