from __future__ import annotations

__all__ = ["SimstringMatcher", "SimstringMatcherRule", "SimstringMatcherNormalization"]

import dataclasses
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional
from typing_extensions import Literal

import yaml

from medkit.text.ner._base_simstring_matcher import (
    BaseSimstringMatcher,
    BaseSimstringMatcherRule,
    BaseSimstringMatcherNormalization,
    build_simstring_matcher_databases,
)


_RULES_DB_FILENAME = "rules.db"
_SIMSTRING_DB_FILENAME = "simstring"


class SimstringMatcherRule(BaseSimstringMatcherRule):
    """
    Rule to use with :class:`~.SimstringMatcher`

    Attributes
    ----------
    term:
        Term to match using similarity-based fuzzy matching
    label:
        Label to use for the entities created when a match is found
    normalization:
        Optional list of normalization attributes that should be attached to the
        entities created
    """

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> SimstringMatcherRule:
        return SimstringMatcherRule(
            term=data["term"],
            label=data["label"],
            id=data["id"],
            normalizations=[
                SimstringMatcherNormalization.from_dict(n)
                for n in data["normalizations"]
            ],
        )


class SimstringMatcherNormalization(BaseSimstringMatcherNormalization):
    """
    Descriptor of normalization attributes to attach to entities
    created from a :class:`~.SimstringMatcherRule`

    Attributes
    ----------
    kb_name:
        The name of the knowledge base we are referencing. Ex: "umls"
    kb_version:
        The name of the knowledge base we are referencing. Ex: "202AB"
    id:
        The id of the entity in the knowledge base, for instance a CUI
    """

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> SimstringMatcherNormalization:
        return SimstringMatcherNormalization(
            kb_name=data["kb_name"],
            kb_version=data["kb_version"],
            id=data["id"],
            term=data["term"],
        )


class SimstringMatcher(BaseSimstringMatcher):
    """
    Entity matcher relying on string similarity

    Uses the `simstring` fuzzy matching algorithm
    (http://chokkan.org/software/simstring/).
    """

    def __init__(
        self,
        rules: List[SimstringMatcherRule],
        threshold: float = 0.9,
        min_length: int = 3,
        max_length: int = 30,
        similarity: Literal["cosine", "dice", "jaccard", "overlap"] = "jaccard",
        attrs_to_copy: Optional[List[str]] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        rules:
            Rules to use for matching entities.
        min_length:
            Minimum number of chars in matched entities.
        max_length:
            Maximum number of chars in matched entities.
        threshold:
            Minimum similarity (between 0.0 and 1.0) between a rule term and the
            text of an entity matched on that rule.
        similarity:
            Similarity metric to use.
        lowercase:
            Whether to use lowercased versions of rule terms and input entities.
        normalize_unicode:
            Whether to use ASCII-only versions of rules terms and input entities
            (non-ASCII chars replaced by closest ASCII chars).
        attrs_to_copy:
            Labels of the attributes that should be copied from the source
            segment to the created entity. Useful for propagating context
            attributes (negation, antecedent, etc).
        name:
            Name describing the matcher (defaults to the class name).
        uid:
            Identifier of the matcher.
        """

        self._temp_dir = tempfile.TemporaryDirectory()
        rules_db_file = Path(self._temp_dir.name) / _RULES_DB_FILENAME
        simstring_db_file = Path(self._temp_dir.name) / _SIMSTRING_DB_FILENAME

        build_simstring_matcher_databases(
            simstring_db_file,
            rules_db_file,
            rules,
        )

        super().__init__(
            simstring_db_file=simstring_db_file,
            rules_db_file=rules_db_file,
            threshold=threshold,
            min_length=min_length,
            max_length=max_length,
            similarity=similarity,
            attrs_to_copy=attrs_to_copy,
            name=name,
            uid=uid,
        )

    @staticmethod
    def load_rules(
        path_to_rules: Path, encoding: Optional[str] = None
    ) -> List[SimstringMatcherRule]:
        """
        Load all rules stored in a yml file

        Parameters
        ----------
        path_to_rules
            Path to a yml file containing a list of mappings with the same
            structure as :class:`~.SimstringMatcherRule`
        encoding
            Encoding of the file to open

        Returns
        -------
        List[SimstringMatcherRule]
            List of all the rules in `path_to_rules`, can be used to init a
            :class:`~.SimstringMatcher`
        """

        class Loader(yaml.Loader):
            pass

        def construct_mapping(loader, node):
            data = loader.construct_mapping(node)
            if "kb_name" in data:
                return SimstringMatcherNormalization(**data)
            else:
                return SimstringMatcherRule(**data)

        Loader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )

        with open(path_to_rules, encoding=encoding) as f:
            rules = yaml.load(f, Loader=Loader)
        return rules

    @staticmethod
    def save_rules(
        rules: List[SimstringMatcherRule],
        path_to_rules: Path,
        encoding: Optional[str] = None,
    ):
        """
        Store rules in a yml file

        Parameters
        ----------
        rules
            The rules to save
        path_to_rules
            Path to a yml file that will contain the rules
        encoding
            Encoding of the yml file
        """

        with open(path_to_rules, mode="w", encoding=encoding) as f:
            rules_data = [dataclasses.asdict(r) for r in rules]
            rules = yaml.safe_dump(rules_data, f)
