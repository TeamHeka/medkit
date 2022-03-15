from __future__ import annotations

__all__ = ["RegexpMatcher", "RegexpMatcherRule", "RegexpMatcherNormalization"]

import dataclasses
from pathlib import Path
import re
from typing import Any, Iterator, List, Optional, Tuple

import yaml


from medkit.core import (
    Collection,
    Attribute,
    Origin,
    ProcessingDescription,
    RuleBasedAnnotator,
)
from medkit.core.text import (
    Entity,
    Segment,
    TextDocument,
    span_utils,
)


@dataclasses.dataclass
class RegexpMatcherRule:
    """
    Regexp-based rule to use with `RegexpMatcher`

    Attributes
    ----------
    regexp:
        The regexp pattern used to match entities
    label:
        The label to attribute to entities created based on this rule
    id:
        Unique identifier of the rule to store in the metadata of the entities
    version:
        Version string to store in the metadata of the entities
    index_extract:
        If the regexp has groups, the index of the group to use to extract
        the entity
    case_sensitive:
        Wether to ignore case when running `regexp and `regexp_exclude`
    regexp_exclude:
        An optional exclusion pattern. Note that this exclusion pattern will
        executed on the whole input annotation, so when relying on `regexp_exclude`
        make sure the input annotations passed to `RegexpMatcher` are "local"-enough
        (sentences or syntagmes) rather than the whole text or paragraphs
    normalization:
        Optional list of normalization attributes that should be attached to
        the entities created
    """

    regexp: str
    label: str
    id: str
    version: str
    index_extract: int = 0
    case_sensitive: bool = False
    regexp_exclude: Optional[str] = None
    normalizations: List[RegexpMatcherNormalization] = dataclasses.field(
        default_factory=lambda: []
    )


@dataclasses.dataclass
class RegexpMatcherNormalization:
    """
    Descriptor of normalization attributes to attach to entities
    created from a `RegexpMatcherRule`

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
    id: Any


_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "regexp_matcher_default_rules.yml"


class RegexpMatcher(RuleBasedAnnotator):
    """Entity annotator relying on regexp-based rules"""

    def __init__(
        self,
        input_label,
        rules: Optional[List[RegexpMatcherRule]] = None,
        proc_id: Optional[str] = None,
    ):
        """
        Instantiate the regexp matcher

        Parameters
        ----------
        input_label:
            The input label of the segment annotations to use as input.
            NB: other type of annotations such as entities are not supported
        rules:
            The set of rules to use when matching entities. If none provided,
            the rules in "regexp_matcher_default_rules.yml" will be used
        proc_id:
            Identifier of the tokenizer
        """
        self.input_label = input_label
        if rules is None:
            rules = self.load_rules(_PATH_TO_DEFAULT_RULES)
        self.rules = rules

        config = dict(input_label=input_label, rules=rules)
        self._description = ProcessingDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def annotate(self, collection: Collection):
        """
        Process a collection of documents for identifying entities

        Entities and optional attributes annotations are added to the text document.

        Parameters
        ----------
        collection:
            The collection of documents to process. Only TextDocuments will be processed.
        """
        for doc in collection.documents:
            if isinstance(doc, TextDocument):
                self.annotate_document(doc)

    def annotate_document(self, doc: TextDocument):
        """
        Process a document for identifying entities

        Entities and optional attributes annotations are added to the text document.

        Parameters
        ----------
        document:
            The text document to process
        """
        input_ann_ids = doc.segments.get(self.input_label)
        if input_ann_ids is None:
            return
        input_anns = [doc.get_annotation_by_id(id) for id in input_ann_ids]
        output_anns_and_attrs = self._process_input_annotations(input_anns)
        for output_ann, output_attrs in output_anns_and_attrs:
            doc.add_annotation(output_ann)
            for attribute in output_attrs:
                doc.add_annotation(attribute)

    def _process_input_annotations(
        self, input_anns: List[Segment]
    ) -> Iterator[Tuple[Entity, List[Attribute]]]:
        """
        Create a entity annotation and optional attribute annotations
        for each entity detected in `input_anns`

        Parameters
        ----------
        input_anns:
            List of input annotations to process

        Yields
        ------
        Entity:
            Created entity annotations
        List[Attribute]:
            Created attribute annotations attached to each entity
            (might be empty)
        """
        for input_ann in input_anns:
            for rule in self.rules:
                yield from self._match(rule, input_ann)

    def _match(
        self, rule: RegexpMatcherRule, input_ann: Segment
    ) -> Iterator[Tuple[Entity, List[Attribute]]]:
        flags = 0 if rule.case_sensitive else re.IGNORECASE

        for match in re.finditer(rule.regexp, input_ann.text, flags):
            if rule.regexp_exclude is not None:
                # note that we apply regexp_exclude to the whole input_annotation,
                # so we might have a match in a part of the text unrelated to the current
                # match
                # we could check if we have any exclude match overlapping with
                # the current match but that wouldn't work for all cases
                exclude_match = re.search(rule.regexp_exclude, input_ann.text, flags)
                if exclude_match is not None:
                    continue
            # extract raw span list from regex match range
            text, spans = span_utils.extract(
                input_ann.text, input_ann.spans, [match.span(rule.index_extract)]
            )
            metadata = dict(
                id_regexp=rule.id,
                version=rule.version,
                # TODO decide how to handle that in medkit
                # **syntagme.attributes,
            )
            entity = Entity(
                label=rule.label,
                text=text,
                spans=spans,
                origin=Origin(
                    processing_id=self.description.id, ann_ids=[input_ann.id]
                ),
                metadata=metadata,
            )

            # add normalization attribute for each normalization descriptor
            # of the rule
            # TODO should we have a NormalizationAttribute class
            # with specific fields (name, id, version) ?
            attributes = [
                Attribute(
                    origin=Origin(
                        processing_id=self.description.id, ann_ids=[input_ann.id]
                    ),
                    label=norm.kb_name,
                    target_id=entity.id,
                    value=norm.id,
                    metadata=dict(version=norm.kb_version),
                )
                for norm in rule.normalizations
            ]

            yield entity, attributes

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)

    @staticmethod
    def load_rules(path_to_rules) -> List[RegexpMatcherRule]:
        """
        Load all rules stored in a yml file

        Parameters
        ----------
        path_to_rules:
            Path to a yml file containing a list of mappings
            with the same structure as `RegexpMatcherRule`

        Returns
        -------
        List[RegexpMatcherRule]
            List of all the rules in `path_to_rules`,
            can be used to init a `RegexpMatcher`
        """

        class Loader(yaml.Loader):
            pass

        def construct_mapping(loader, node):
            data = loader.construct_mapping(node)
            if "kb_name" in data:
                return RegexpMatcherNormalization(**data)
            else:
                return RegexpMatcherRule(**data)

        Loader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )

        with open(path_to_rules, mode="r") as f:
            rules = yaml.load(f, Loader=Loader)
        return rules
