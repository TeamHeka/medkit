__all__ = ["DoccanoTask", "DoccanoIDEConfig", "DoccanoInputConverter"]

import dataclasses
import enum
import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from medkit.core import Attribute, OperationDescription, ProvTracer, generate_id
from medkit.core.text import Entity, Relation, Span, TextDocument
from medkit.io._doccano_utils import (
    DoccanoDocRelationExtraction,
    DoccanoDocSeqLabeling,
    DoccanoDocTextClassification,
)

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
        doccano_doc = DoccanoDocRelationExtraction.from_dict(
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
        doccano_doc = DoccanoDocSeqLabeling.from_dict(
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
        doccano_doc = DoccanoDocTextClassification.from_dict(
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
