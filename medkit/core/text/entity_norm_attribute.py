from __future__ import annotations

__all__ = ["EntityNormAttribute"]

import dataclasses
from typing import Any, ClassVar, Dict, Optional
from typing_extensions import Self

from medkit.core import dict_conv
from medkit.core.attribute import Attribute


@dataclasses.dataclass(init=False)
class EntityNormAttribute(Attribute):
    """
    Normalization attribute linking an entity to an ID in a knowledge base

    Attributes
    ----------
    uid:
        Identifier of the attribute
    label:
        The attribute label, always set to :attr:`EntityNormAttribute.LABEL`
    value:
        Value of the attribute. Built by concatenating `kb_name` with `kb_id` when
        available, otherwise `term` is used.
    kb_name:
        Name of the knowledge base (ex: "icd"). Should always be provided except
        in special cases when we just want to store a normalized term.
    kb_id:
        ID in the knowledge base to which the annotation should be linked.
        Should always be provided except in special cases when we just want to
        store a normalized term.
    kb_version:
        Optional version of the knowledge base.
    term:
        Optional normalized version of the entity text.
    score:
        Optional score reflecting confidence of this link.
    metadata:
        Metadata of the attribute
    """

    kb_name: Optional[str]
    kb_id: Optional[Any]
    kb_version: Optional[str]
    term: Optional[str]
    score: Optional[float]

    LABEL: ClassVar[str] = "NORMALIZATION"
    """
    Label used for all normalization attributes
    """

    def __init__(
        self,
        kb_name: Optional[str],
        kb_id: Optional[Any],
        kb_version: Optional[str] = None,
        term: Optional[str] = None,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        if kb_id is None and term is None:
            raise ValueError("Must provide at least kb_id or term")

        if kb_id is not None:
            if kb_name is not None:
                value = f"{kb_name}:{kb_id}"
            else:
                value = kb_name
        else:
            value = term

        super().__init__(label=self.LABEL, value=value, metadata=metadata, uid=uid)

        self.kb_name = kb_name
        self.kb_id = kb_id
        self.kb_version = kb_version
        self.term = term
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        norm_dict = dict(
            uid=self.uid,
            label=self.label,
            kb_name=self.kb_name,
            kb_id=self.kb_id,
            kb_version=self.kb_version,
            term=self.term,
            score=self.score,
            metadata=self.metadata,
        )
        dict_conv.add_class_name_to_data_dict(self, norm_dict)
        return norm_dict

    @classmethod
    def from_dict(cls, norm_dict: Dict[str, Any]) -> Self:
        dict_conv.check_class_matches_data_dict(cls, norm_dict)
        return cls(
            uid=norm_dict["uid"],
            label=norm_dict["label"],
            kb_name=norm_dict["kb_name"],
            kb_id=norm_dict["kb_id"],
            kb_version=norm_dict["kb_version"],
            term=norm_dict["term"],
            score=norm_dict["score"],
            metadata=norm_dict["metadata"],
        )
