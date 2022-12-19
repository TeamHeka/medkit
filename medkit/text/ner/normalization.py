__all__ = ["EntityNormalization", "UMLSNormalization"]

from typing import Any, Dict, List, Optional


class EntityNormalization:
    """Normalization linking an entity to an ID in a knowledge base."""

    def __init__(
        self,
        kb_name: Optional[str],
        kb_id: Optional[Any],
        kb_version: Optional[str] = None,
        term: Optional[str] = None,
        score: Optional[float] = None,
    ):
        """
        Parameters:
        -----------
        kb_name:
            Name of the knowledge base (ex: "icd"). Should always be provided
            except in special cases when we just want to store a normalized
            term.
        kb_id:
            ID in the knowledge base to which the annotation should be linked.
            Should always be provided except in special cases when we just want
            to store a normalized term.
        kb_version:
            Optional version of the knowledge base
        term:
            Normalized version of the entity text
        score:
            Optional score reflecting confidence of this link
        """
        self.kb_name = kb_name
        self.kb_id = kb_id
        self.kb_version = kb_version
        self.term = term
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            kb_name=self.kb_name,
            kb_id=self.kb_id,
            kb_version=self.kb_version,
            term=self.term,
            score=self.score,
        )


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
        Parameters:
        -----------
        cui:
            CUI to which the annotation should be linked.
        umls_version:
            Optional version of the UMLS database (ex: "202AB").
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
        data = super().to_dict()
        data.update(sem_types=self.sem_types)
        return data
