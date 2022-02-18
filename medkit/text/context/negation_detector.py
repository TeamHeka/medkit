__all__ = ["NegationDetector"]

import re
from typing import List, Optional

from medkit.core import Origin, Attribute, OperationDescription, RuleBasedAnnotator
from medkit.core.text import Segment


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
            neg = _detect_negation(segment.text)
            attr = Attribute(
                origin=Origin(operation_id=self.description.id, ann_ids=[segment.id]),
                label=self.output_label,
                value=neg == "neg",
            )
            segment.attrs.append(attr)


def _detect_negation(phrase):
    phrase_low = phrase.lower()
    if len(re.findall(r"[a-z]", phrase_low)) == 0:
        return "aff"

    # fmt: off
    # pas * d
    if (
        ((re.findall(r"(^|[^a-z])pas\s([a-z']*\s*){0,2}d", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z]*\s){0,2}doute", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}elimin[eé]", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}exclure", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}probl[eèé]me", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}soucis", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}objection", phrase_low) == []) & \
            (re.findall(r"\sne reviens\s+pas", phrase_low) == [])) | \
        # pas * pour
        ((re.findall(r"(^|[^a-z])pas\s([a-z']*\s*){0,2}pour", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z]*\s){0,2}doute", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}pour\s+[eé]limine", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}pour\s+exclure", phrase_low) == [])) | \
        # (ne|n') (l'|la|le)? * pas
        ((re.findall(r"(^|[^a-z])n(e\s+|'\s*)(l[ae]\s+|l'\s*)?([a-z']*\s*){0,2}pas[^a-z]", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z]*\s){0,2}doute", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}elimin[eèé]", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}exclure", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}soucis", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}objection", phrase_low) == []) & \
            (re.findall(r"\sne reviens\s+pas", phrase_low) == [])) | \
        # sans
        ((re.findall(r"(^|[^a-z])sans\s", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])sans\s+doute", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s+elimine", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s+probl[eéè]me", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s+soucis", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s+objection", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s+difficult", phrase_low) == [])) | \
        # aucun
        ((re.findall(r"aucun", phrase_low) != []) & \
            (re.findall(r"aucun\s+doute", phrase_low) == []) & \
            (re.findall(r"aucun\s+probleme", phrase_low) == []) & \
            (re.findall(r"aucune\s+objection", phrase_low) == [])) | \
        # élimine
        ((re.findall(r"(^|[^a-z])[eé]limine", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}elimine", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s*([a-z']*\s*){0,2}elimine", phrase_low) == [])) | \
        # éliminant
        ((re.findall(r"(^|[^a-z])[eé]liminant", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])[eé]liminant\s*pas[^a-z]", phrase_low) == [])) | \
        # infirme
        ((re.findall(r"(^|[^a-z])infirm[eé]", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}infirmer", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s*([a-z']*\s*){0,2}infirmer", phrase_low) == [])) | \
        # infirmant
        ((re.findall(r"(^|[^a-z])infirmant", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])infirmant\s*pas[^a-z]", phrase_low) == [])) | \
        # exclu
        ((re.findall(r"(^|[^a-z])exclu[e]?[s]?[^a-z]", phrase_low) != []) & \
            (re.findall(r"(^|[^a-z])pas\s*([a-z']*\s*){0,2}exclure", phrase_low) == []) & \
            (re.findall(r"(^|[^a-z])sans\s*([a-z']*\s*){0,2}exclure", phrase_low) == [])) | \
        # misc
        (re.findall(r"(^|[^a-z])jamais\s[a-z]*\s*d", phrase_low) != []) | \

        (re.findall(r"orient[eèé]\s+pas\s+vers", phrase_low) != []) | \

        (re.findall(r"orientant\s+pas\s+vers", phrase_low) != []) | \

        (re.findall(r"(^|[^a-z])ni\s", phrase_low) != []) | \

        (re.findall(r":\s*non[^a-z]", phrase_low) != []) | \

        (re.findall(r"^\s*non[^a-z]+$", phrase_low) != []) | \

        (re.findall(r":\s*aucun", phrase_low) != []) | \

        (re.findall(r":\s*exclu", phrase_low) != []) | \

        (re.findall(r":\s*absen[ct]", phrase_low) != []) | \

        (re.findall(r"absence\s+d", phrase_low) != []) | \

        (re.findall(r"\snegati", phrase_low) != []) | \

        ((re.findall(r"(^|[^a-z])normale?s?[^a-z]", phrase_low) != []) & \
            (re.findall(r"pas\s+normale?s?\s", phrase_low) == [])) | \

        ((re.findall(r"(^|[^a-z])normaux", phrase_low) != []) & \
            (re.findall(r"pas\s+normaux", phrase_low) == []))
    ):
        return "neg"
    else:
        return "aff"
    # fmt: on
