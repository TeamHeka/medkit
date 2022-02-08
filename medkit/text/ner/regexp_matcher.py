from __future__ import annotations

__all__ = ["RegexpMatcher", "RegexpMatcherRule", "RegexpMatcherNormalization"]

import dataclasses
import json
from pathlib import Path
import re
from typing import Any, List, Optional
import uuid

from medkit.core.text import Entity, TextBoundAnnotation, TextDocument
import medkit.core.text.span as span_utils


@dataclasses.dataclass
class RegexpMatcherRule:
    id: str
    label: str
    regexp: str
    version: str
    regexp_exclude: Optional[str] = None
    index_extract: int = 0
    case_sensitive: bool = False
    comment: Optional[str] = None
    normalizations: List[RegexpMatcherNormalization] = dataclasses.field(
        default_factory=lambda: []
    )


@dataclasses.dataclass
class RegexpMatcherNormalization:
    kb_name: str
    kb_version: str
    id: Any


_PATH_TO_DEFAULT_RULES = Path(__file__).parent / "list_regexp.json"


class RegexpMatcher:
    def __init__(
        self, input_label, list_regexp: Optional[List[RegexpMatcherRule]] = None
    ):
        self.input_label = input_label
        if list_regexp is None:
            list_regexp = self.load_rules(_PATH_TO_DEFAULT_RULES)
        self.list_regexp = list_regexp

    def annotate_document(self, doc: TextDocument):
        syntagme_ids = doc.segments[self.input_label]

        for rex in self.list_regexp:
            if len(syntagme_ids) == 0:
                return

            for syntagme_id in syntagme_ids:
                syntagme = doc.get_annotation_by_id(syntagme_id)
                self.find_matches(doc, rex, syntagme)

    def find_matches(
        self,
        doc: TextDocument,
        rex: RegexpMatcherRule,
        syntagme: TextBoundAnnotation,
        snippet_size=60,
    ):
        if rex.case_sensitive:
            reflags = 0
        else:
            reflags = re.IGNORECASE

        for m in re.finditer(rex.regexp, syntagme.text, flags=reflags):
            if m is not None:

                # filter if match regexp_exclude
                if rex.regexp_exclude is not None:
                    exclude_match = re.search(rex.regexp_exclude, syntagme.text)
                    if exclude_match is not None:
                        continue

                text, spans = span_utils.extract(
                    syntagme.text, syntagme.spans, [m.span(rex.index_extract)]
                )

                if doc.text is not None:
                    spans_normalized = span_utils.normalize_spans(spans)
                    snippet_start = min(s.start for s in spans_normalized)
                    snippet_end = max(s.end for s in spans_normalized)
                    snippet_start = max(snippet_start - snippet_size, 0)
                    snippet_end = max(snippet_end + snippet_size, len(doc.text))
                    snippet_value = doc.text[snippet_start:snippet_end]
                else:
                    snippet_value = None

                entity = Entity(
                    label=rex.label,
                    text=text,
                    spans=spans,
                    metadata={
                        "id_regexp": rex.id,
                        "version": rex.version,
                        "snippet": snippet_value,
                        # TODO decide how to handle that in medkit
                        # **syntagme.attributes,
                    },
                    origin_id=uuid.uuid1(),
                    # FIXME store this provenance info somewhere
                    # source_id=syntagme.id,
                )
                doc.add_annotation(entity)

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
