from __future__ import annotations

__all__ = [
    "BaseSimstringMatcher",
    "BaseSimstringMatcherRule",
    "BaseSimstringMatcherNormalization",
    "build_simstring_matcher_databases",
]

import dataclasses
import itertools
import logging
import math
from pathlib import Path
import re
from typing import Iterator, List, Optional, Tuple, Union
from typing_extensions import Literal
import shelve

from pysimstring import simstring
from unidecode import unidecode

from medkit.core.text import (
    Entity,
    NEROperation,
    Segment,
    EntityNormAttribute,
    span_utils,
)
from medkit.text.ner import UMLSNormAttribute


logger = logging.getLogger(__name__)

_TOKENIZATION_PATTERN = re.compile(r"[\w]+|[^\w ]")
_SIMILARITY_MAP = {
    "cosine": simstring.cosine,
    "dice": simstring.dice,
    "jaccard": simstring.jaccard,
    "overlap": simstring.overlap,
}


@dataclasses.dataclass
class BaseSimstringMatcherRule:
    """
    Rule to use with :class:`~.BaseSimstringMatcher`

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

    term: str
    label: str
    normalizations: List[BaseSimstringMatcherNormalization] = dataclasses.field(
        default_factory=list
    )


@dataclasses.dataclass
class BaseSimstringMatcherNormalization:
    """
    Descriptor of normalization attributes to attach to entities
    created from a `~.BaseSimstringMatcherRule`

    Attributes
    ----------
    kb_name:
        The name of the knowledge base we are referencing. Ex: "umls"
    kb_version:
        The name of the knowledge base we are referencing. Ex: "202AB"
    id:
        The id of the entity in the knowledge base, for instance a CUI
    """

    kb_name: str
    kb_version: str
    id: Union[int, str]
    term: Optional[str] = None


@dataclasses.dataclass
class _Match:
    start: int
    end: int
    term: str
    score: float

    @property
    def length(self):
        return self.end - self.start

    def overlaps(self, other: _Match):
        return (other.start <= self.end) and (other.end >= self.start)


class BaseSimstringMatcher(NEROperation):
    """
    Base class for entity matcher using the `simtring` fuzzy matching algorithm
    (also used by `QuickUMLS`).
    """

    def __init__(
        self,
        simstring_db_file: Path,
        rules_db_file: Path,
        lowercase: bool = True,
        normalize_unicode: bool = True,
        threshold: float = 0.7,
        min_length: int = 3,
        max_length: int = 15,
        similarity: Literal["cosine", "dice", "jaccard", "overlap"] = "jaccard",
        attrs_to_copy: Optional[List[str]] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        simstring_db_file:
            Simstring database to use
        rules_db_file:
            Rules database (in python shelve format) mapping matched terms to
            correponding rules
        lowercase:
            Wether to use lowercased versions of rule terms and input entities.
        normalize_unicode:
            Wether to ASCII-only versions of rules terms and input entities
            (non-ASCII chars replaced by closest ASCII chars).
        min_length:
            Minimum number of chars in matched entities.
        max_length:
            Maximum number of chars in matched entities.
        threshold:
            Minimum similarity (between 0.0 and 1.0) between a rule term and the
            text of an entity matched on that rule.
        similarity:
            Similarity metric to use.
        attrs_to_copy:
            Labels of the attributes that should be copied from the source
            segment to the created entity. Useful for propagating context
            attributes (negation, antecedent, etc).
        name:
            Name describing the matcher (defaults to the class name).
        uid:
            Identifier of the matcher.
        """

        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        assert similarity in _SIMILARITY_MAP.keys(), (
            f"Invalid similarity '{similarity}', must be one of"
            f" {list(_SIMILARITY_MAP.keys())}"
        )

        if attrs_to_copy is None:
            attrs_to_copy = []

        self.lowercase = lowercase
        self.normalize_unicode = normalize_unicode
        self.min_length = min_length
        self.max_length = max_length
        self.similarity = similarity
        self.attrs_to_copy = attrs_to_copy

        self._simstring_db_reader = simstring.reader(str(simstring_db_file))
        self._simstring_db_reader.measure = _SIMILARITY_MAP[similarity]
        self._simstring_db_reader.threshold = threshold

        self._rules_db = shelve.open(str(rules_db_file), flag="r")

    def _preprocess_segment_text(self, text: str) -> str:
        """Preprocessing segment text according to the `lowercase` and
        `normalize_unicode` init params"""

        if self.lowercase:
            text = text.lower()

        if self.normalize_unicode:
            ascii_text = unidecode(text)
            if len(ascii_text) != len(text):
                logger.warning(
                    "Lengths of unicode text and generated ascii text are different. "
                    "Please, pre-process input text before running SimstringMatcher\n\n"
                    f"Unicode:{text} (length: {len(text)})\n"
                    f"Ascii: {ascii_text} (length: {len(ascii_text)})\n"
                )
            else:
                text = ascii_text

        return text

    def run(self, segments: List[Segment]) -> List[Entity]:
        """
        Return entities (with optional normalization attributes) matched in `segments`

        Parameters
        ----------
        segments:
            List of segments into which to look for matches

        Returns
        -------
        entities: List[Entity]:
            Entities found in `segments` (with optional normalization
            attributes)
        """

        return [
            entity
            for segment in segments
            for entity in self._find_matches_in_segment(segment)
        ]

    def _find_matches_in_segment(self, segment: Segment) -> Iterator[Entity]:
        """Return an iterator to the entities matched in a segment"""

        text = segment.text
        matches = []
        for start, end in self._build_candidate_ranges(
            text, self.min_length, self.max_length
        ):
            candidate_text = self._preprocess_segment_text(text[start:end])
            matched_terms = self._simstring_db_reader.retrieve(candidate_text)
            for term in matched_terms:
                score = _get_similarity_score(term, candidate_text, self.similarity)
                match = _Match(start, end, term, score=score)
                matches.append(match)

        # when matches overlap, keep only longest
        matches = self._filter_overlapping_matches(matches)

        for match in matches:
            yield self._build_entity(segment, match)

    @staticmethod
    def _build_candidate_ranges(
        text: str, min_length: int, max_length: int
    ) -> Iterator[Tuple[int, int]]:
        """From a string, generate all candidate matches (by tokenizing it and then
        re-concatenating tokens) and return their ranges. Based on the QuickUMLS
        code.

        Parameters
        ----------
        text:
            Text from which to generate candidates
        min_length:
            Min length of a candidate, in characters
        max_length:
            Max length of a candidate, in characters

        Returns
        -------
        Iterator[Tuple[int, int]]
            Iterator over ranges of candidate matches

        Example
        -------
        >>> text = "I have type 2 diabetes"
        >>> ranges = SimstringMatcher._build_candidate_ranges(text, 2, 15)
        >>> candidates = [text[slice(*r)] for r in ranges]
        >>> candidates
        ['I have', 'I have type', 'have', 'have type', 'type', 'type 2 diabetes', 'diabetes']
        """

        # simple tokenization, good enough for our usecase and less fuss than using spacy
        matches = [(m.group(0), m.span()) for m in _TOKENIZATION_PATTERN.finditer(text)]
        tokens, ranges = zip(*matches)
        nb_tokens = len(tokens)

        # iterate over non-empty tokens
        for i in range(nb_tokens):
            start_token = tokens[i]
            if not start_token[0].isalnum():
                continue
            # build candidate by appending next tokens
            start = ranges[i][0]
            for j in itertools.count(start=i):
                # reached end of available tokens
                if j >= nb_tokens:
                    break
                end_token = tokens[j]
                # next token is empty, skip candidate
                if not end_token[0].isalnum():
                    continue
                end = ranges[j][1]
                length = end - start
                # candidate is too short, skip
                if length < min_length:
                    continue
                # candidate is too long, stop appending tokens
                if length > max_length:
                    break
                yield (start, end)

    @staticmethod
    def _filter_overlapping_matches(matches: List[_Match]) -> List[_Match]:
        """
        Remove overlapping matches by keeping longest matches among overlapping matches
        """

        matches.sort(key=lambda m: m.score, reverse=True)
        matches_filtered = []
        for match in matches:
            if any(match.overlaps(prev_match) for prev_match in matches_filtered):
                continue
            matches_filtered.append(match)

        return matches_filtered

    def _build_entity(self, segment: Segment, match: _Match) -> Entity:
        """Build an entity from a match in a segment"""

        # extract text and spans corresponding to match
        text, spans = span_utils.extract(
            segment.text, segment.spans, [(match.start, match.end)]
        )

        # retrieve rule corresponding to matched term
        rule = self._rules_db[match.term]
        label = rule.label

        # create entity
        entity = Entity(label=label, text=text, spans=spans)
        if self._prov_tracer is not None:
            self._prov_tracer.add_prov(
                entity, self.description, source_data_items=[segment]
            )

        # propagate attrs_to_copy from segment to new entity
        for attr_label in self.attrs_to_copy:
            for attr in segment.attrs.get(label=attr_label):
                copied_attr = attr.copy()
                entity.attrs.add(copied_attr)
                if self._prov_tracer is not None:
                    self._prov_tracer.add_prov(copied_attr, self.description, [attr])

        # create normalization attributes for each
        # normalization descriptor of the rule
        for norm in rule.normalizations:
            norm_attr = self._create_norm_attr(norm, match.score)
            entity.attrs.add(norm_attr)

            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    norm_attr, self.description, source_data_items=[segment]
                )

        return entity

    @staticmethod
    def _create_norm_attr(
        norm: BaseSimstringMatcherNormalization, score: float
    ) -> EntityNormAttribute:
        """Create a normalization attribute based on the normalization descriptor of a rule
        """

        if norm.kb_name == "umls":
            norm_attr = UMLSNormAttribute(
                cui=norm.id,
                umls_version=norm.kb_version,
                term=norm.term,
                score=score,
            )
        else:
            norm_attr = EntityNormAttribute(
                kb_name=norm.kb_name,
                kb_id=norm.id,
                kb_version=norm.kb_version,
                term=norm.term,
                score=score,
            )
        return norm_attr


def build_simstring_matcher_databases(
    simstring_db_file: Path,
    rules_db_file: Path,
    rules: Iterator[BaseSimstringMatcherRule],
    lowercase: bool,
    normalize_unicode: bool,
):
    simstring_db_writer = simstring.writer(
        str(simstring_db_file),
        # the following params are copy/pasted from QuickUMLS
        3,  # unit of character n-grams
        False,  # represent begin and end of strings in n-grams
        True,  # use unicode mode
    )

    rules_db = shelve.open(str(rules_db_file), flag="n")

    # add rules to databases
    for rule in rules:
        term_to_match = rule.term

        # apply preprocessing
        if lowercase:
            term_to_match = term_to_match.lower()
        if normalize_unicode:
            term_to_match = unidecode(term_to_match)

        # add to simstring db
        simstring_db_writer.insert(term_to_match)
        # add to rules db
        rules_db[term_to_match] = rule
    simstring_db_writer.close()
    rules_db.sync()
    rules_db.close()


# based on https://github.com/Georgetown-IR-Lab/QuickUMLS/blob/master/quickumls/toolbox.py


def _get_similarity_score(text_1, text_2, similarity_name, ngram_size=3):
    """
    The MIT License (MIT)

    Copyright (c) 2019 Georgetown Information Retrieval Lab

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """

    def _make_ngrams(text, ngram_size):
        n = len(text) if len(text) < ngram_size else ngram_size
        return set(text[i : i + n] for i in range(len(text) - n + 1))

    ngrams_1 = _make_ngrams(text_1, ngram_size)
    ngrams_2 = _make_ngrams(text_2, ngram_size)
    nb_ngrams_1 = len(ngrams_1)
    nb_ngrams_2 = len(ngrams_2)
    nb_ngrams_common = len(ngrams_1.intersection(ngrams_2))

    if similarity_name == "dice":
        return 2 * nb_ngrams_common / (nb_ngrams_1 + nb_ngrams_2)
    if similarity_name == "jaccard":
        return nb_ngrams_common / (nb_ngrams_1 + nb_ngrams_2 - nb_ngrams_common)
    if similarity_name == "cosine":
        return nb_ngrams_common / math.sqrt(nb_ngrams_1 * nb_ngrams_2)
    assert similarity_name == "overlap"
    return nb_ngrams_common
