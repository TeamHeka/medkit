__all__ = ["HypothesisDetector"]

import re
from typing import List, Optional

from medkit.core import generate_id, Attribute
from medkit.core.text import Segment
from medkit.text.context._verb_list import VERB_LIST


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
        proc_id: Optional[str] = None,
    ):
        """Instantiate the hypothesis detector

        Parameters
        ----------
        output_label:
            The label of the created attributes
        proc_id:
            Identifier of the detector
        """
        if proc_id is None:
            proc_id = generate_id()

        self.id: str = proc_id
        self.output_label: str = output_label

        self.verbs_hypo = self._load_verbs_hypo()

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
            sentence_array = re.split(r"[^\w0-9.\']+", phrase_low)

            inter_hypo = list(set(self.verbs_hypo) & set(sentence_array))

            if len(inter_hypo) > 0:
                is_hypothesis = True
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

        hyp_attr = Attribute(
            label=self.output_label,
            value=is_hypothesis,
        )
        return hyp_attr

    @staticmethod
    def _load_verbs_hypo():
        verbs_hypo = []
        for verb in VERB_LIST:
            verbs_hypo += verb["conditionnel"]["présent"]
            verbs_hypo += verb["indicatif"]["futur simple"]

        verbs_hypo = set(verbs_hypo)
        return verbs_hypo
