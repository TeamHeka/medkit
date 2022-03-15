__all__ = ["QuickUMLSMatcher"]

from pathlib import Path
from typing import Dict, Iterator, List, Literal, NamedTuple, Optional, Tuple, Union

from quickumls import QuickUMLS
import quickumls.constants

from medkit.core import Collection, Origin, ProcessingDescription, RuleBasedAnnotator
from medkit.core.text import (
    Attribute,
    Entity,
    Segment,
    TextDocument,
    span_utils,
)


# workaround for https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/68
for key, value in quickumls.constants.SPACY_LANGUAGE_MAP.items():
    ext = "_core_web_sm" if value == "en" else "_core_news_sm"
    quickumls.constants.SPACY_LANGUAGE_MAP[key] = value + ext


class _QuickUMLSInstall(NamedTuple):
    version: str
    language: str
    lowercase: bool
    normalize_unicode: bool


class QuickUMLSMatcher(RuleBasedAnnotator):
    """Entity annotator relying on QuickUMLS.

    This annotator requires a QuickUMLS installation performed
    with `python -m quickumls.install` with flags corresponding
    to the params `language`, `version`, `lowercase` and `normalize_unicode`
    passed at init. QuickUMLS installations must be registered with the
    `add_install` class method.

    For instance, if we want to use `QuickUMLSMatcher` with a french
    lowercase QuickUMLS install based on UMLS version 2021AB,
    we must first create this installation with:

        python -m quickumls.install --language FRE --lowercase /path/to/umls/2021AB/data /path/to/quick/umls/install

    then register this install with:

        QuickUMLSMatcher.add_install(
            "/path/to/quick/umls/install",
            version="2021AB",
            language="FRE",
            lowercase=True,
        )

    and finally instantiate the matcher with:

        matcher = QuickUMLSMatcher(
            input_label,
            version="2021AB",
            language="FRE",
            lowercase=True,
        )

    This mechanism makes it possible to store in the ProcessingDescription
    how the used QuickUMLS was created, and to reinstantiate the same matcher
    on a different environment if a similar install is available.
    """

    _install_paths: Dict[_QuickUMLSInstall, str] = {}

    @classmethod
    def add_install(
        cls,
        path: Union[str, Path],
        version: str,
        language: str,
        lowercase: bool = False,
        normalize_unicode: bool = False,
    ):
        """Register path and settings of a QuickUMLS installation performed
        with `python -m quickumls.install`

        Parameters
        ----------
        path:
            The path to the destination folder passed to the install command
        version:
            The version of the UMLS database, for instance "2021AB"
        language:
            The language flag passed to the install command, for instance "ENG"
        lowercase:
            Wether the --lowercase flag was passed to the install command
            (concepts are lowercased to increase recall)
        normalize_unicode:
            Wether the --normalize-unicode flag was passed to the install command
            (non-ASCII chars in concepts are converted to the closest ASCII chars)
        """
        install = _QuickUMLSInstall(version, language, lowercase, normalize_unicode)
        cls._install_paths[install] = str(path)

    @classmethod
    def clear_installs(cls):
        """Remove all QuickUMLS installation registered with `add_install`"""
        cls._install_paths.clear()

    @classmethod
    def _get_path_to_install(
        cls,
        version: str,
        language: str,
        lowercase: bool = False,
        normalize_unicode: bool = False,
    ) -> str:
        """Find a QuickUMLS install with corresponding settings

        The QuickUMLS install must have been previously registered with `add_install`.
        """
        install = _QuickUMLSInstall(version, language, lowercase, normalize_unicode)
        path = cls._install_paths.get(install)
        if path is None:
            raise Exception(
                "Couldn't find any Quick- UMLS install "
                f"for {version=}, {language=}, {lowercase=}, {normalize_unicode=}.\n"
                f"Registered installs: {cls._install_paths}"
            )
        return path

    def __init__(
        self,
        input_label: str,
        version: str,
        language: str,
        lowercase: bool = False,
        normalize_unicode: bool = False,
        overlapping: Literal["length", "score"] = "length",
        threshold: float = 0.9,
        window: int = 5,
        similarity: Literal["dice", "jaccard", "cosine", "overlap"] = "jaccard",
        accepted_semtypes: List[str] = quickumls.constants.ACCEPTED_SEMTYPES,
        proc_id: Optional[str] = None,
    ):
        """Instantiate the QuickUMLS matcher

        Parameters
        ----------
        input_label:
            The input label of the segment annotations to use as input.
            NB: other type of annotations such as entities are not supported
        version:
            UMLS version of the QuickUMLS install to use, for instance "2021AB"
            Will be used to decide with QuickUMLS to use
        language:
            Language flag of the QuickUMLS install to use, for instance "ENG".
            Will be used to decide with QuickUMLS to use
        lowercase:
            Wether to use a QuickUMLS install with lowercased concepts
            Will be used to decide with QuickUMLS to use
        normalize_unicode:
            Wether to use a QuickUMLS install with non-ASCII chars concepts
            converted to the closest ASCII chars.
            Will be used to decide with QuickUMLS to use
        overlapping:
            Criteria for sorting multiple potential matches (cf QuickUMLS doc)
        threshold:
            Minimum similarity (cf QuickUMLS doc)
        window:
            Max number of tokens per match (cf QuickUMLS doc)
        similarity:
            Similarity measure to use (cf QuickUMLS doc)
        accepted_semtypes:
            UMLS semantic types that matched concepts should belong to (cf QuickUMLS doc).
        """

        self.input_label = input_label
        self.version = version
        path_to_install = self._get_path_to_install(
            version, language, lowercase, normalize_unicode
        )
        self._matcher = QuickUMLS(
            quickumls_fp=path_to_install,
            overlapping_criteria=overlapping,
            threshold=threshold,
            window=window,
            similarity_name=similarity,
            accepted_semtypes=accepted_semtypes,
        )
        assert (
            self._matcher.language_flag == language
            and self._matcher.to_lowercase_flag == lowercase
            and self._matcher.normalize_unicode_flag == normalize_unicode
        ), "Inconsistent QuickUMLS install flags"

        config = dict(
            input_label=input_label,
            language=language,
            version=version,
            lowercase=lowercase,
            normalize_unicode=normalize_unicode,
            overlapping=overlapping,
            threshold=threshold,
            similarity=similarity,
            window=window,
            accepted_semtypes=accepted_semtypes,
        )
        self._description = ProcessingDescription(
            id=proc_id, name=self.__class__.__name__, config=config
        )

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def annotate(self, collection: Collection):
        """Process a collection of documents for identifying entities

        Entities and corresponding normalization attributes are added to the text document.

        Parameters
        ----------
        collection:
            The collection of documents to process. Only TextDocuments will be processed.
        """
        for doc in collection.documents:
            if isinstance(doc, TextDocument):
                self.annotate_document(doc)

    def annotate_document(self, doc: TextDocument):
        """Process a document for identifying entities

        Entities and corresponding normalization attributes are added to the text document.

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
        for output_ann, output_attr in output_anns_and_attrs:
            doc.add_annotation(output_ann)
            doc.add_annotation(output_attr)

    def _process_input_annotations(
        self, input_anns: List[Segment]
    ) -> Iterator[Tuple[Entity, Attribute]]:
        """Create a entity annotation and a corresponding normalization attribute
        for each entity detected in `input_anns`

        Parameters
        ----------
        input_anns:
            List of input annotations to process

        Yields
        ------
        Entity:
            Created entity annotation
        Attribute:
            Created normalization attribute attached to each entity
        """
        for input_ann in input_anns:
            yield from self._match(input_ann)

    def _match(self, input_ann: Segment) -> Iterator[Tuple[Entity, Attribute]]:
        matches = self._matcher.match(input_ann.text)
        for match_candidates in matches:
            # only the best matching CUI (1st match candidate) is returned
            # TODO should we create a normalization attributes for each CUI instead?
            match = match_candidates[0]

            text, spans = span_utils.extract(
                input_ann.text, input_ann.spans, [(match["start"], match["end"])]
            )
            entity = Entity(
                label=match["term"],
                text=text,
                spans=spans,
                origin=Origin(processing_id=self.description.id, ann_ids=[input_ann.id])
                # TODO decide how to handle that in medkit
                # **input_entity.attributes,
            )

            # TODO force now we consider the version, score and semtypes
            # to be just extra informational metadata
            # We might need to reconsider this if these items
            # are actually accessed in other "downstream" processing modules
            metadata = dict(
                version=self.version,
                score=match["similarity"],
                sem_types=list(match["semtypes"]),
            )
            attribute = Attribute(
                label="umls",
                target_id=entity.id,
                value=match["cui"],
                metadata=metadata,
                origin=Origin(
                    processing_id=self.description.id, ann_ids=[input_ann.id]
                ),
            )
            yield entity, attribute

    @classmethod
    def from_description(cls, description: ProcessingDescription):
        return cls(proc_id=description.id, **description.config)
