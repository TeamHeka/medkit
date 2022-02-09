from __future__ import annotations

__all__ = ["RegexpMatcher", "RegexpMatcherRule", "RegexpMatcherNormalization"]

import dataclasses
from pathlib import Path
import re
from typing import Any, Iterator, List, Optional, Union

import yaml

from medkit.core import Collection
from medkit.core.processing import ProcessingDescription, RuleBasedAnnotator
from medkit.core.text import Attribute, Entity, TextBoundAnnotation, TextDocument
import medkit.core.text.span as span_utils


@dataclasses.dataclass
class RegexpMatcherRule:
    regexp: str
    label: str
    id: str
    version: str
    index_extract: int = 0
    case_sensitive: bool = False
    regexp_exclude: Optional[str] = None
    comment: Optional[str] = None
    normalizations: List[RegexpMatcherNormalization] = dataclasses.field(
        default_factory=lambda: []
    )


@dataclasses.dataclass
class RegexpMatcherNormalization:

    kb_name: str
    kb_version: str
    id: Any


_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "regexp_matcher_default_rules.yml"


class RegexpMatcher(RuleBasedAnnotator):
    def __init__(self, input_label, rules: Optional[List[RegexpMatcherRule]] = None):
        self.input_label = input_label
        if rules is None:
            rules = self.load_rules(_PATH_TO_DEFAULT_RULES)
        self.rules = rules

        config = dict(input_label=input_label, rules=rules)
        self._description = ProcessingDescription(
            name=self.__class__.__name__, config=config
        )

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def annotate(self, collection: Collection):
        for doc in collection.documents:
            if isinstance(doc, TextDocument):
                self.annotate_document(doc)

    def annotate_document(self, doc: TextDocument):
        input_ann_ids = doc.segments.get(self.input_label)
        if input_ann_ids is not None:
            input_anns = [doc.get_annotation_by_id(id) for id in input_ann_ids]
            output_anns = self._process_input_annotations(input_anns)
            for output_ann in output_anns:
                doc.add_annotation(output_ann)

    def _process_input_annotations(
        self, input_anns: List[TextBoundAnnotation]
    ) -> Iterator[Union[Entity, Attribute]]:
        for input_ann in input_anns:
            for rule in self.rules:
                yield from self._match(rule, input_ann)

    def _match(
        self, rule: RegexpMatcherRule, input_ann: TextBoundAnnotation
    ) -> Iterator[Union[Entity, Attribute]]:
        flags = 0 if rule.case_sensitive else re.IGNORECASE

        for match in re.finditer(rule.regexp, input_ann.text, flags):
            if rule.regexp_exclude is not None:
                exclude_match = re.search(rule.regexp_exclude, input_ann.text, flags)
                if exclude_match is not None:
                    continue

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
                origin_id=self.description.id,
                metadata=metadata,
                # FIXME store this provenance info somewhere
                # source_id=syntagme.id,
            )
            yield entity

            for normalization in rule.normalizations:
                # TODO should we have a NormalizationAttribute class
                # with specific fields (name, id, version) ?
                attribute = Attribute(
                    origin_id=self.description.id,
                    label=normalization.kb_name,
                    target_id=entity.id,
                    value=normalization.id,
                    metadata=dict(version=normalization.kb_version),
                )
                yield attribute

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)

    @staticmethod
    def load_rules(path_to_rules) -> List[RegexpMatcherRule]:
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
