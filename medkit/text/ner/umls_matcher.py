from __future__ import annotations

__all__ = ["UMLSMatcher"]

import dataclasses
import logging
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union
from typing_extensions import Literal

import yaml

from medkit.text.ner import umls_utils
from medkit.text.ner._base_simstring_matcher import (
    BaseSimstringMatcher,
    BaseSimstringMatcherRule,
    BaseSimstringMatcherNormalization,
    build_simstring_matcher_databases,
)

_CACHE_PARAMS_FILENAME = "params.yml"
_RULES_DB_FILENAME = "rules"
_SIMSTRING_DB_FILENAME = "simstring"

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class _UMLSMatcherCacheParams:
    umls_version: str
    language: str
    allowed_semgroups: List[str]
    labels_by_semgroup: Dict[str]
    lowercase: bool
    normalize_unicode: bool


class UMLSMatcher(BaseSimstringMatcher):
    """
    Entity annotator identifying UMLS concepts using the `simstring` fuzzy
    matching algorithm (http://chokkan.org/software/simstring/).

    This operation is heavily inspired by the `QuickUMLS` library
    (https://github.com/Georgetown-IR-Lab/QuickUMLS)
    """

    _SEMGROUP_BY_SEMTYPE = None

    def __init__(
        self,
        umls_dir: Union[str, Path],
        cache_dir: Union[str, Path],
        language: str,
        threshold: float = 0.7,
        min_length: int = 3,
        max_length: int = 30,
        similarity: Literal["cosine", "dice", "jaccard", "overlap"] = "jaccard",
        lowercase: bool = True,
        normalize_unicode: bool = False,
        allowed_semgroups: Optional[List[str]] = None,
        output_labels_by_semgroup: Optional[Union[str, Dict[str, str]]] = None,
        attrs_to_copy: Optional[List[str]] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        umls_dir:
            Path to the UMLS directory containing the MRCONSO.RRF and
            MRSTY.RRF files.
        cache_dir:
            Path to the directory into which the umls database will be cached.
            If it doesn't exist yet, the database will be automatically
            generated (it can take a long time) and stored there, ready to be
            reused on further instantiations. If it already exists, a check will
            be done to make sure the params used when the database was generated
            are consistent with the params of the current instance. If you want
            to rebuild the database with new params using the same cache dir,
            you will have to manually delete it first.
        language:
            Language to consider as found in the MRCONSO.RRF file. Example:
            `"FRE"`. Will trigger a regeneration of the database if changed.
        min_length:
            Minimum number of chars in matched entities.
        max_length:
            Maximum number of chars in matched entities.
        threshold:
            Minimum similarity threshold (between 0.0 and 1.0) between a UMLS term
            and the text of a matched entity.
        similarity:
            Similarity metric to use.
        lowercase:
            Whether to use lowercased versions of rule terms and input entities.
            Will trigger a regeneration of the database if changed.
        normalize_unicode:
            Whether to use ASCII-only versions of rules terms and input entities
            (non-ASCII chars replaced by closest ASCII chars). Will trigger a
            regeneration of the database if changed.
        allowed_semgroups:
            Ids of UMLS semantic groups that matched concepts should belong to.
            cf
            https://lhncbc.nlm.nih.gov/semanticnetwork/download/sg_archive/SemGroups-v04.txt
            If `None` provided, all concepts can be matched. Will trigger a
            regeneration of the database if changed.
            Example: `["DISO", "PROC"]`
        output_labels_by_semgroup:
            By default, ~`medkit.text.ner.umls.SEMGROUP_LABELS` will be used as
            entity labels. Use this parameter to override them. Example:
            `{"DISO": "problem", "PROC": "test}`. If `output_labels_by_semgroup`
            is a string, all entities will use this string as label instead.
            Will trigger a regeneration of the database if changed.
        attrs_to_copy:
            Labels of the attributes that should be copied from the source
            segment to the created entity. Useful for propagating context
            attributes (negation, antecedent, etc)
        name:
            Name describing the matcher (defaults to the class name).
        uid:
            Identifier of the matcher.
        """

        umls_dir = Path(umls_dir)
        cache_dir = Path(cache_dir)

        # check that values of allowed_semgroups are valid semgroup ids
        if allowed_semgroups is not None:
            for semgroup in allowed_semgroups:
                if semgroup not in umls_utils.SEMGROUPS:
                    raise ValueError(
                        f"Unknown semgroup: {semgroup}. Should be one of"
                        f" {umls_utils.SEMGROUPS}"
                    )

        cache_dir.mkdir(parents=True, exist_ok=True)

        labels_by_semgroup = self._get_labels_by_semgroup(output_labels_by_semgroup)

        cache_params = _UMLSMatcherCacheParams(
            umls_version=umls_utils.guess_umls_version(umls_dir),
            language=language,
            allowed_semgroups=allowed_semgroups,
            labels_by_semgroup=labels_by_semgroup,
            lowercase=lowercase,
            normalize_unicode=normalize_unicode,
        )

        cache_params_file = cache_dir / _CACHE_PARAMS_FILENAME
        simstring_db_file = cache_dir / _SIMSTRING_DB_FILENAME
        rules_db_file = cache_dir / _RULES_DB_FILENAME

        if cache_params_file.exists():
            with open(cache_params_file) as fp:
                existing_cache_params = _UMLSMatcherCacheParams(**yaml.safe_load(fp))
            if cache_params != existing_cache_params:
                raise Exception(
                    f"Cache directory {cache_dir} contains database pre-computed"
                    f" with different params: {existing_cache_params} vs"
                    f" {cache_params}"
                )
        else:
            logger.info(
                "Building simstring database from UMLS terms, this may take a while"
            )
            rules = self._build_rules(
                umls_dir,
                language,
                lowercase,
                normalize_unicode,
                allowed_semgroups,
                labels_by_semgroup,
            )

            build_simstring_matcher_databases(simstring_db_file, rules_db_file, rules)

            with open(cache_params_file, mode="w") as fp:
                yaml.safe_dump(dataclasses.asdict(cache_params), fp)

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

    @classmethod
    def _get_labels_by_semgroup(
        cls, output_labels: Union[None, str, Dict[str, str]]
    ) -> Dict[str, str]:
        """
        Return a mapping giving the label to use for all entries of a given semgroup

        output_labels:
            Optional mapping of labels to use. Can be used to override the default
            labels. If `output_labels` is a single string, it will be used as a unique
            label for all semgroups

        Returns
        -------
        Dict[str, str]:
            A mapping with semgroups as keys and corresponding label as values
        """

        if output_labels is None:
            return umls_utils.SEMGROUP_LABELS

        if isinstance(output_labels, str):
            return {key: output_labels for key in umls_utils.SEMGROUP_LABELS}

        # check that the keys of output_labels are valid semgroup ids
        for semgroup in output_labels.keys():
            if semgroup not in umls_utils.SEMGROUPS:
                raise ValueError(
                    f"Unknown semgroup: {semgroup}. Should be one of"
                    f" {umls_utils.SEMGROUPS}"
                )

        label_mapping = umls_utils.SEMGROUP_LABELS.copy()
        label_mapping.update(output_labels)
        return label_mapping

    @classmethod
    def _build_rules(
        cls,
        umls_dir: Path,
        language: str,
        lowercase: bool,
        normalize_unicode: bool,
        allowed_semgroups: Optional[List[str]],
        labels_by_semgroup: Dict[str, str],
    ) -> Iterator[BaseSimstringMatcherRule]:
        """
        Create rules for all UMLS entries (filtered by `language` and
        `allowed_semgroups`) with appropriate labels (based on
        `labels_by_semgroup`)
        """

        # get iterator to all UMLS entries
        entries_iter = umls_utils.load_umls_entries(
            mrconso_file=umls_dir / "MRCONSO.RRF",
            mrsty_file=umls_dir / "MRSTY.RRF",
            languages=[language],
            show_progress=True,
        )

        version = umls_utils.guess_umls_version(umls_dir)

        for entry in entries_iter:
            # filter out entries not belonging to allowed semgroups
            semgroups = entry.semgroups
            if allowed_semgroups is not None:
                semgroups = [s for s in semgroups if s in allowed_semgroups]
                if len(semgroups) == 0:
                    continue

            # take label corresponding to semgroup (1st semgroup if multiple)
            semgroup = semgroups[0]
            label = labels_by_semgroup[semgroup]

            # perform UMLS-specific cleaning, lowercase and normalize unicode
            # will be handled by BaseSimstringMatcher
            term = umls_utils.preprocess_term_to_match(
                entry.term,
                lowercase=False,
                normalize_unicode=False,
            )

            norm = BaseSimstringMatcherNormalization(
                kb_name="umls", kb_version=version, id=entry.cui, term=entry.term
            )
            rule = BaseSimstringMatcherRule(
                term=term,
                label=label,
                case_sensitive=not lowercase,
                unicode_sensitive=not normalize_unicode,
                normalizations=[norm],
            )
            yield rule
