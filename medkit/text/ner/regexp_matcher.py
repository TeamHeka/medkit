from __future__ import annotations

__all__ = ["RegexpMatcher", "RegexpMatcherRule", "RegexpMatcherNormalization"]

import dataclasses
import json
from pathlib import Path
import re
from typing import Any, Iterator, List, Optional

from medkit.core.processing import ProcessingDescription
from medkit.core.text import Entity, TextBoundAnnotation, TextDocument
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


_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "regexp_matcher_default_rules.json"


@dataclasses.dataclass
class RegexpMatcherNormalization:

    kb_name: str
    kb_version: str
    id: Any


class RegexpMatcher:
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

    def annotate_document(self, doc: TextDocument):
        input_ann_ids = doc.segments.get(self.input_label)
        if input_ann_ids is not None:
            input_anns = [doc.get_annotation_by_id(id) for id in input_ann_ids]
            output_entities = self._process_input_annotations(input_anns)
            for output_entity in output_entities:
                doc.add_annotation(output_entity)

    def _process_input_annotations(
        self, input_anns: List[TextBoundAnnotation]
    ) -> Iterator[Entity]:
        for input_ann in input_anns:
            for rule in self.rules:
                yield from self._match(rule, input_ann)

    def _match(
        self, rule: RegexpMatcherRule, input_ann: TextBoundAnnotation
    ) -> Iterator[Entity]:
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

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)

    @staticmethod
    def load_rules(path_to_rules) -> List[RegexpMatcherRule]:
        def hook(data):
            if "kb_name" in data:
                return RegexpMatcherNormalization(**data)
            else:
                return RegexpMatcherRule(**data)

        with open(path_to_rules, mode="r") as f:
            rules = json.load(f, object_hook=hook)
        return rules
