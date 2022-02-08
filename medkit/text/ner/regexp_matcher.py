__all__ = ["RegexpMatcher", "RegexpMatcherRule"]

import dataclasses
import json
from pathlib import Path
import re
import uuid

from medkit.core.text import Entity, TextBoundAnnotation, TextDocument
import medkit.core.text.span as span_utils


@dataclasses.dataclass
class RegexpMatcherRule:
    id_regexp: str
    libelle: str
    regexp: str
    regexp_exclude: str
    version: str
    index_extract: str = ""
    filtre_document: str = ""
    casesensitive: str = ""
    comment: str = ""
    date_modification: str = ""
    list_cui: str = ""
    icd10: str = ""
    regexp_v1: str = ""
    regexp_v2: str = ""
    regexp_v3: str = ""
    regexp_exclude_v1: str = ""
    regexp_exclude_v2: str = ""
    regexp_exclude_v3: str = ""
    deprecated: str = ""
    refresh: str = ""


class RegexpMatcher:
    def __init__(self, input_label, regexp_file=None):
        self.input_label = input_label
        if regexp_file is None:
            regexp_file = str(Path(__file__).parent / "list_regexp.json")
        if type(regexp_file) is str:
            with open(regexp_file, "r") as f:
                self.list_regexp = json.load(
                    f, object_hook=lambda d: RegexpMatcherRule(**d)
                )
        elif type(regexp_file) is list:
            self.list_regexp = regexp_file
        else:
            raise Exception("wrong type for regexp_file")

    def annotate_document(self, doc: TextDocument):
        syntagme_ids = doc.segments[self.input_label]

        for rex in self.list_regexp:
            if len(syntagme_ids) == 0:
                return

            # filter on document by filtre_document
            if doc.text is not None and rex.filtre_document != "":
                docmatch = re.search(rex.filtre_document, doc.text)
                if docmatch is None:
                    continue

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
        if rex.casesensitive == "yes":
            reflags = 0
        else:
            reflags = re.IGNORECASE

        for m in re.finditer(rex.regexp, syntagme.text, flags=reflags):
            if m is not None:

                # filter if match regexp_exclude
                if rex.regexp_exclude != "":
                    exclude_match = re.search(rex.regexp_exclude, syntagme.text)
                    if exclude_match is not None:
                        continue

                if rex.index_extract != "":
                    i = int(rex.index_extract)
                else:
                    i = 0
                text, spans = span_utils.extract(
                    syntagme.text, syntagme.spans, [m.span(i)]
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
                    label=rex.libelle,
                    text=text,
                    spans=spans,
                    metadata={
                        "id_regexp": rex.id_regexp,
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
