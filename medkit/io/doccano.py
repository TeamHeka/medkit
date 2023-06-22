__all__ = [
    "DoccanoTask",
    "DoccanoIDEConfig",
    "DoccanoInputConverter",
    "DoccanoOutputConverter",
]

import dataclasses
import enum
import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from medkit.core import Attribute, OperationDescription, ProvTracer, generate_id
from medkit.core.text import Entity, Relation, Span, TextDocument, span_utils
from medkit.io import _doccano_utils as utils

from medkit.io._common import get_anns_by_type

logger = logging.getLogger(__name__)


class DoccanoTask(enum.Enum):
    """Supported doccano tasks. The task defines
    the type of document to convert.

    Attributes
    ----------
    TEXT_CLASSIFICATION
        Documents with a category
    RELATION_EXTRACTION
        Documents with entities and relations (including IDs)
    SEQUENCE_LABELING
        Documents with entities in tuples
    """

    TEXT_CLASSIFICATION = "text_classification"
    RELATION_EXTRACTION = "relation_extraction"
    SEQUENCE_LABELING = "sequence_labeling"


@dataclasses.dataclass
class DoccanoIDEConfig:
    """A class representing the IDE configuration in doccano client.
    The default values are the default values used in doccano.

    Attributes
    ----------
    column_text:
        Name or key representing the text
    column_label:
        Name or key representing the labels
    category_label:
        Label of attribute to add for text classification
    """

    column_text: str = "text"
    column_label: str = "label"
    category_label: str = "doccano_category"


class DoccanoInputConverter:
    """Convert doccano files (.JSONL) containing annotations for a given task.

    For each line a :class:`~medkit.core.text.TextDocument` will be created.
    The doccano files can be load from a directory with zip files or from a jsonl file.
    """

    def __init__(
        self,
        task: DoccanoTask,
        config: Optional[DoccanoIDEConfig] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        task:
            The doccano task for the input converter
        config:
            Optional IDEConfig to define default values in doccano IDE.
            This config can change the name of the text field or labels.
        uid:
            Identifier of the converter.
        """
        if uid is None:
            uid = generate_id()

        if config is None:
            config = DoccanoIDEConfig()

        self.uid = uid
        self.config = config
        self.task = task
        self._prov_tracer: Optional[ProvTracer] = None

    def set_prov_tracer(self, prov_tracer: ProvTracer):
        """Enable provenance tracing.

        Parameters
        ----------
        prov_tracer:
            The provenance tracer used to trace the provenance.
        """
        self._prov_tracer = prov_tracer

    @property
    def description(self) -> OperationDescription:
        """Contains all the input converter init parameters."""
        return OperationDescription(
            uid=self.uid,
            name=self.__class__.__name__,
            class_name=self.__class__.__name__,
            config=dict(task=self.task.value),
        )

    def load_from_directory_zip(self, dir_path: str) -> List[TextDocument]:
        """Load doccano files from zip files in a directory.
        The zip files should contain a JSONL file with doccano annotations.

        Parameters
        ----------
        dir_path:
            The path to the directory containing zip files.

        Returns
        -------
        List[TextDocument]
            A list of TextDocuments
        """
        documents = []
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, zip_file in enumerate(Path(dir_path).glob("*.zip")):
                with ZipFile(zip_file) as zip_file:
                    filename = zip_file.namelist()[0]
                    zip_file.extract(filename, f"{tmpdir}/tmpfile_{i}")

            for input_file in Path(tmpdir).rglob("*.jsonl"):
                documents.extend(self.load_from_file(input_file))

        if len(documents) == 0:
            logger.warning(f"No .zip nor .jsonl found in '{dir_path}'")

        logger.info(f"Created {len(documents)}  documents from {dir_path}")
        return documents

    def load_from_file(self, input_file) -> List[TextDocument]:
        """Load doccano files from a JSONL file

        Parameters
        ----------
        input_file:
            The path to the JSON file containing doccano annotations

        Returns
        -------
        List[TextDocument]
            A list of TextDocuments
        """
        documents = []

        with open(input_file, encoding="utf-8") as fp:
            for line in fp:
                doc_line = json.loads(line)
                doc = self.parse_doc_line(doc_line)
                documents.append(doc)
        return documents

    def parse_doc_line(self, doc_line: Dict[str, Any]) -> TextDocument:
        """Parse a doc_line into a TextDocument depending on the task

        Parameters
        ----------
        doc_line:
            A dictionary representing an annotation from doccano

        Returns
        -------
        TextDocument
            A document with parsed annotations.
        """
        if self.task == DoccanoTask.RELATION_EXTRACTION:
            return self._parse_doc_line_relation_extraction(doc_line=doc_line)
        if self.task == DoccanoTask.TEXT_CLASSIFICATION:
            return self._parse_doc_line_text_classification(doc_line=doc_line)
        if self.task == DoccanoTask.SEQUENCE_LABELING:
            return self._parse_doc_line_seq_labeling(doc_line=doc_line)

    def _parse_doc_line_relation_extraction(
        self, doc_line: Dict[str, Any]
    ) -> TextDocument:
        """Parse a dictionary and return a TextDocument with entities and relations

        Parameters
        ----------
        doc_line:
            Dictionary with doccano annotation

        Returns
        -------
        TextDocument
            The document with annotations
        """
        doccano_doc = utils.DoccanoDocRelationExtraction.from_dict(
            doc_line, column_text=self.config.column_text
        )

        anns_by_doccano_id = dict()
        for doccano_entity in doccano_doc.entities.values():
            text = doccano_doc.text[
                doccano_entity.start_offset : doccano_entity.end_offset
            ]
            entity = Entity(
                text=text,
                label=doccano_entity.label,
                spans=[Span(doccano_entity.start_offset, doccano_entity.end_offset)],
                metadata=dict(doccano_id=doccano_entity.id),
            )
            # entities can have the same id as relations
            # add a prefix to identify entities
            anns_by_doccano_id[f"E{doccano_entity.id}"] = entity

            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    entity, self.description, source_data_items=[]
                )

        for doccano_relation in doccano_doc.relations.values():
            relation = Relation(
                label=doccano_relation.type,
                source_id=anns_by_doccano_id[f"E{doccano_relation.from_id}"].uid,
                target_id=anns_by_doccano_id[f"E{doccano_relation.to_id}"].uid,
                metadata=dict(doccano_id=doccano_relation.id),
            )
            anns_by_doccano_id[doccano_relation.id] = relation

            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    relation, self.description, source_data_items=[]
                )

        metadata = doccano_doc.metadata.copy()
        metadata.update(dict(doccano_id=doccano_doc.id))

        doc = TextDocument(
            text=doccano_doc.text,
            anns=list(anns_by_doccano_id.values()),
            metadata=metadata,
        )

        return doc

    def _parse_doc_line_seq_labeling(self, doc_line: Dict[str, Any]) -> TextDocument:
        """Parse a dictionary and return a TextDocument with entities

        Parameters
        ----------
        doc_line:
            Dictionary with doccano annotation.

        Returns
        -------
        TextDocument
            The document with annotations
        """
        doccano_doc = utils.DoccanoDocSeqLabeling.from_dict(
            doc_line,
            column_text=self.config.column_text,
            column_label=self.config.column_label,
        )
        anns = []
        for doccano_entity in doccano_doc.entities:
            text = doccano_doc.text[
                doccano_entity.start_offset : doccano_entity.end_offset
            ]
            entity = Entity(
                text=text,
                label=doccano_entity.label,
                spans=[Span(doccano_entity.start_offset, doccano_entity.end_offset)],
            )
            anns.append(entity)

            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    entity, self.description, source_data_items=[]
                )

        doc = TextDocument(
            text=doccano_doc.text,
            anns=anns,
            metadata=doccano_doc.metadata,
        )
        return doc

    def _parse_doc_line_text_classification(
        self, doc_line: Dict[str, Any]
    ) -> TextDocument:
        """Parse a dictionary and return a TextDocument with an attribute.
        The attribute will be in its raw segment.

        Parameters
        ----------
        doc_line:
            Dictionary with doccano annotation.

        Returns
        -------
        TextDocument
            The document with its category
        """
        doccano_doc = utils.DoccanoDocTextClassification.from_dict(
            doc_line,
            column_text=self.config.column_text,
            column_label=self.config.column_label,
        )
        attr = Attribute(label=self.config.category_label, value=doccano_doc.label)

        if self._prov_tracer is not None:
            self._prov_tracer.add_prov(attr, self.description, source_data_items=[])

        doc = TextDocument(text=doccano_doc.text)
        doc.raw_segment.attrs.add(attr)
        return doc


class DoccanoOutputConverter:
    """Convert medkit files to doccano files (.JSONL) for a given task.

    For each :class:`~medkit.core.text.TextDocument` a jsonline will be created.
    """

    def __init__(
        self,
        task: DoccanoTask,
        anns_labels: Optional[List[str]] = None,
        attr: Optional[str] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        task:
            The doccano task for the input converter
        anns_labels:
            Labels of medkit annotations to convert into docccano annotations.
            If `None` (default) all the annotations (entities and relations)
            will be converted.
        attr:
            Label of medkit attribute for text classification.
        uid:
            Identifier of the converter.
        """
        if uid is None:
            uid = generate_id()

        self.uid = uid
        self.task = task
        self.anns_labels = anns_labels
        self.attr = attr

        if self.attr is None and task == DoccanoTask.TEXT_CLASSIFICATION:
            logger.warning(
                "You should specify an attribute label for text classification. The"
                " first attribute of the raw segment will be used as label for the"
                " exported annotations."
            )

    @property
    def description(self) -> OperationDescription:
        config = dict(anns_labels=self.anns_labels, attr=self.attr)
        return OperationDescription(
            uid=self.uid, class_name=self.__class__.__name__, config=config
        )

    def save(self, docs: List[TextDocument], dir_path: str):
        """Convert and save a list of TextDocuments into a doccano file (.JSONL)

        Parameters
        ----------
        docs:
            List of medkit doc objects to convert
        dir_path:
            String or path object to save the generated files
        """

        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        with open(dir_path / "all.jsonl", mode="w", encoding="utf-8") as fp:
            for i, medkit_doc in enumerate(docs):
                doc_line = self._convert_doc_by_task(i, medkit_doc)
                fp.write(json.dumps(doc_line) + "\n")

    def _convert_doc_by_task(
        self, idx: int, medkit_doc: TextDocument
    ) -> Dict[str, Any]:
        """Convert a TextDocument into a dictionary depending on the task

        Parameters
        ----------
        medkit_doc:
            Document to convert

        Returns
        -------
        Dict[str,Any]
            Dictionary with doccano annotation
        """
        if self.task == DoccanoTask.RELATION_EXTRACTION:
            return self._convert_doc_relation_extraction(idx=idx, medkit_doc=medkit_doc)
        if self.task == DoccanoTask.TEXT_CLASSIFICATION:
            return self._convert_doc_text_classification(medkit_doc=medkit_doc)
        if self.task == DoccanoTask.SEQUENCE_LABELING:
            return self._convert_doc_seq_labeling(medkit_doc=medkit_doc)

    def _convert_doc_relation_extraction(
        self, idx: int, medkit_doc: TextDocument
    ) -> Dict[str, Any]:
        """Convert a TextDocument to a doc_line compatible
        with the doccano relation extraction task

        Parameters
        ----------
        medkit_doc:
            Document to convert, it may contain entities and relations

        Returns
        -------
        Dict[str,Any]
            Dictionary with doccano annotation. It may contain
            text, entities and relations
        """
        nb_entity, nb_relation = 0, 0
        entities, relations = dict(), dict()

        anns_by_type = get_anns_by_type(medkit_doc, self.anns_labels)

        for medkit_entity in anns_by_type["entities"]:
            spans = span_utils.normalize_spans(medkit_entity.spans)
            doccano_entity = utils.DoccanoEntity(
                id=nb_entity,
                start_offset=spans[0].start,
                end_offset=spans[-1].end,
                label=medkit_entity.label,
            )
            entities[medkit_entity.uid] = doccano_entity
            nb_entity += 1

        for medkit_relation in anns_by_type["relations"]:
            subj = entities.get(medkit_relation.source_id)
            obj = entities.get(medkit_relation.target_id)

            if subj is None or obj is None:
                logger.warning(
                    f"Ignore relation {medkit_relation.uid}. Entity source/target was"
                    " no found"
                )
                continue

            doccano_relation = utils.DoccanoRelation(
                id=nb_relation,
                from_id=subj.id,
                to_id=obj.id,
                type=medkit_relation.label,
            )
            relations[medkit_relation.uid] = doccano_relation
            nb_relation += 1

        doccano_doc = utils.DoccanoDocRelationExtraction(
            id=idx,
            text=medkit_doc.text,
            entities=entities,
            relations=relations,
            metadata=medkit_doc.metadata,
        )

        return doccano_doc.to_dict()

    def _convert_doc_seq_labeling(self, medkit_doc: TextDocument) -> Dict[str, Any]:
        """Convert a TextDocument to a doc_line compatible
        with the doccano sequence labeling task

        Parameters
        ----------
        medkit_doc:
            Document to convert, it may contain entities and relations

        Returns
        -------
        Dict[str,Any]
            Dictionary with doccano annotation. It may contain
            text ans its label (a list of tuples representing entities)
        """
        anns_by_type = get_anns_by_type(medkit_doc, self.anns_labels)
        entities = []
        for medkit_entity in anns_by_type["entities"]:
            spans = span_utils.normalize_spans(medkit_entity.spans)
            doccano_entity = utils.DoccanoEntityTuple(
                start_offset=spans[0].start,
                end_offset=spans[-1].end,
                label=medkit_entity.label,
            )
            entities.append(doccano_entity)

        doccano_doc = utils.DoccanoDocSeqLabeling(
            text=medkit_doc.text,
            entities=entities,
            metadata=medkit_doc.metadata,
        )

        return doccano_doc.to_dict()

    def _convert_doc_text_classification(
        self, medkit_doc: TextDocument
    ) -> Dict[str, Any]:
        """Convert a TextDocument to a doc_line compatible with
        the doccano text classification task. The attribute to add as a label
        should be in its raw segment.

        Parameters
        ----------
        doc_line:
            Dictionary with doccano annotation.

        Returns
        -------
        Dict[str,Any]
            Dictionary with doccano annotation. It may contain
            text ans its label (a list with its category(str))
        """
        attribute = medkit_doc.raw_segment.attrs.get(label=self.attr)

        if not attribute:
            raise KeyError(
                "The attribute with the corresponding text class was not found. Check"
                " the 'attr', {self.attr} was provided."
            )

        doccano_doc = utils.DoccanoDocTextClassification(
            text=medkit_doc.text,
            label=attribute[0].value,
            metadata=medkit_doc.metadata,
        )
        return doccano_doc.to_dict()
