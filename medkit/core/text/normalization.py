from __future__ import annotations

__all__ = ["EntityNormalization"]

from typing import Any, Dict, Optional

from medkit.core.attribute import AttributeValue
from medkit.core.dict_serialization import dict_serializable


@dict_serializable
class EntityNormalization(AttributeValue):
    """Normalization linking an entity to an ID in a knowledge base.

    To be used as the value of a normalization attribute.
    """

    def __init__(
        self,
        kb_name: Optional[str],
        kb_id: Optional[Any],
        kb_version: Optional[str] = None,
        term: Optional[str] = None,
        score: Optional[float] = None,
    ):
        """
        Parameters
        ----------
        kb_name:
            Name of the knowledge base (ex: "icd"). Should always be provided
            except in special cases when we just want to store a normalized
            term.
        kb_id:
            ID in the knowledge base to which the annotation should be linked.
            Should always be provided except in special cases when we just want
            to store a normalized term.
        kb_version:
            Optional version of the knowledge base.
        term:
            Normalized version of the entity text.
        score:
            Optional score reflecting confidence of this link.
        """
        self.kb_name = kb_name
        self.kb_id = kb_id
        self.kb_version = kb_version
        self.term = term
        self.score = score

    def get_simple_representation(self) -> str:
        # special case when we just have a normalized term
        if self.kb_name is None and self.kb_id is None:
            return self.term

        return f"{self.kb_name}:{self.kb_id}"

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            kb_name=self.kb_name,
            kb_id=self.kb_id,
            kb_version=self.kb_version,
            term=self.term,
            score=self.score,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EntityNormalization:
        return cls(**data)
