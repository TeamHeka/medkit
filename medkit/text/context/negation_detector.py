__all__ = ["NegationDetector", "NegationDetectorRule"]

import dataclasses
import re
from typing import List, Optional

from medkit.core import Origin, Attribute, OperationDescription, RuleBasedAnnotator
from medkit.core.text import Segment


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
        proc_id: Optional[str] = None,
    ):
        """Instantiate the negation detector

        Parameters
        ----------
        output_label:
            The output label of the created annotations
        proc_id:
            Identifier of the detector
        """
        self.output_label = output_label

        config = dict()
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
            neg, rule = _detect_negation(segment.text)
            is_negated = neg == "neg"
            attr = Attribute(
                origin=Origin(operation_id=self.description.id, ann_ids=[segment.id]),
                label=self.output_label,
                value=is_negated,
                metadata=dict(rule_id=rule.id) if is_negated else None,
            )
            segment.attrs.append(attr)


def _detect_negation(phrase):
    phrase_low = phrase.lower()
    if len(re.findall(r"[a-z]", phrase_low)) == 0:
        return "aff", None

    # pas * d
    rule = NegationDetectorRule(
        id="id_neg_pas_d",
        regexp=r"(^|[^a-z])pas\s([a-z']*\s*){0,2}d",
        exclusion_regexps=[
            r"(^|[^a-z])pas\s*([a-z]*\s){0,2}doute",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}elimin[eé]",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}exclure",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}probl[eèé]me",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}soucis",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}objection",
            r"\sne reviens\s+pas",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # pas * pour
    rule = NegationDetectorRule(
        id="id_neg_pas_pour",
        regexp=r"(^|[^a-z])pas\s([a-z']*\s*){0,2}pour",
        exclusion_regexps=[
            r"(^|[^a-z])pas\s*([a-z]*\s){0,2}doute",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}pour\s+[eé]limine",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}pour\s+exclure",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # (ne|n') (l'|la|le)? * pas
    rule = NegationDetectorRule(
        id="id_neg_n_l_pas",
        regexp=r"(^|[^a-z])n(e\s+|'\s*)(l[ae]\s+|l'\s*)?([a-z']*\s*){0,2}pas[^a-z]",
        exclusion_regexps=[
            r"(^|[^a-z])pas\s*([a-z]*\s){0,2}doute",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}elimin[eèé]",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}exclure",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}soucis",
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}objection",
            r"\sne reviens\s+pas",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # sans
    rule = NegationDetectorRule(
        id="id_neg_sans",
        regexp=r"(^|[^a-z])sans\s",
        exclusion_regexps=[
            r"(^|[^a-z])sans\s+doute",
            r"(^|[^a-z])sans\s+elimine",
            r"(^|[^a-z])sans\s+probl[eéè]me",
            r"(^|[^a-z])sans\s+soucis",
            r"(^|[^a-z])sans\s+objection",
            r"(^|[^a-z])sans\s+difficult",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # aucun
    rule = NegationDetectorRule(
        id="id_neg_aucun",
        regexp=r"aucun",
        exclusion_regexps=[
            r"aucun\s+doute",
            r"aucun\s+probleme",
            r"aucune\s+objection",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # élimine
    rule = NegationDetectorRule(
        id="id_neg_elimine",
        regexp=r"(^|[^a-z])[eé]limine",
        exclusion_regexps=[
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}elimine",
            r"(^|[^a-z])sans\s*([a-z']*\s*){0,2}elimine",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # éliminant
    rule = NegationDetectorRule(
        id="id_neg_eliminant",
        regexp=r"(^|[^a-z])[eé]liminant",
        exclusion_regexps=[
            r"(^|[^a-z])[eé]liminant\s*pas[^a-z]",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # infirme
    rule = NegationDetectorRule(
        id="id_neg_infirme",
        regexp=r"(^|[^a-z])infirm[eé]",
        exclusion_regexps=[
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}infirmer",
            r"(^|[^a-z])sans\s*([a-z']*\s*){0,2}infirmer",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # infirmant
    rule = NegationDetectorRule(
        id="id_neg_infirmant",
        regexp=r"(^|[^a-z])infirmant",
        exclusion_regexps=[
            r"(^|[^a-z])infirmant\s*pas[^a-z]",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # exclu
    rule = NegationDetectorRule(
        id="id_neg_exclu",
        regexp=r"(^|[^a-z])exclu[e]?[s]?[^a-z]",
        exclusion_regexps=[
            r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}exclure",
            r"(^|[^a-z])sans\s*([a-z']*\s*){0,2}exclure",
        ],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    # misc
    rule = NegationDetectorRule(
        id="id_neg_jamais", regexp=r"(^|[^a-z])jamais\s[a-z]*\s*d"
    )
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(
        id="id_neg_oriente_pas_vers", regexp=r"orient[eèé]\s+pas\s+vers"
    )
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(
        id="id_neg_orientant_pas_vers", regexp=r"orientant\s+pas\s+vers"
    )
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_ni", regexp=r"(^|[^a-z])ni\s")
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_column_non", regexp=r":\s*non[^a-z]")
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_non", regexp=r"^\s*non[^a-z]+$")
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_column_aucun", regexp=r":\s*aucun")
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_column_exclu", regexp=r":\s*exclu")
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_column_absen", regexp=r":\s*absen[ct]")
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_absence", regexp=r"absence\s+d")
    if _match(phrase_low, rule):
        return "neg", rule
    rule = NegationDetectorRule(id="id_neg_negati", regexp=r"\snegati")
    if _match(phrase_low, rule):
        return "neg", rule

    rule = NegationDetectorRule(
        id="id_neg_normal",
        regexp=r"(^|[^a-z])normale?s?[^a-z]",
        exclusion_regexps=[r"pas\s+normale?s?\s"],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    rule = NegationDetectorRule(
        id="id_neg_normaux",
        regexp=r"(^|[^a-z])normaux",
        exclusion_regexps=[r"pas\s+normaux"],
    )
    if _match(phrase_low, rule):
        return "neg", rule

    return "aff", None


def _match(phrase_low, rule: NegationDetectorRule):
    return re.findall(rule.regexp, phrase_low) != [] and not any(
        re.findall(r, phrase_low) != [] for r in rule.exclusion_regexps
    )
