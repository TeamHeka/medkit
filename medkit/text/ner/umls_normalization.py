from __future__ import annotations

__all__ = ["UMLSNormalization"]

from typing import Any, Dict, List, Optional

from medkit.core import dict_serializable
from medkit.core.text import EntityNormalization


@dict_serializable
class UMLSNormalization(EntityNormalization):
    """Normalization attribute linking an entity to a CUI in the UMLS knowledge base."""

    def __init__(
        self,
        cui: str,
        umls_version: str,
        term: Optional[str] = None,
        score: Optional[float] = None,
        sem_types: Optional[List[str]] = None,
    ):
        """
        Parameters
        ----------
        cui:
            CUI (Concept Unique Identifier) to which the annotation should be linked.
        umls_version:
            Optional version of the UMLS database (ex: "202AB").
        term:
            Normalized version of the entity text.
        score:
            Optional score reflecting confidence of this link.
        sem_types:
            IDs of semantic types of the CUI (ex: ["T047"]).
        """
        super().__init__(
            kb_name="umls",
            kb_id=cui,
            kb_version=umls_version,
            term=term,
            score=score,
        )
        self.sem_types = sem_types

    @property
    def cui(self):
        return self.kb_id

    @property
    def umls_version(self):
        return self.kb_version

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            cui=self.cui,
            umls_version=self.umls_version,
            term=self.term,
            score=self.score,
            sem_types=self.sem_types,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UMLSNormalization:
        return cls(**data)
