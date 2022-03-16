__all__ = ["BratInputConverter"]

import pathlib

from smart_open import open

from medkit.core import Collection, Origin, InputConverter, ProcessingDescription
from medkit.core.text import TextDocument, Entity, Relation, Attribute
import medkit.io._brat_utils as brat_utils


class BratInputConverter(InputConverter):
    """Class in charge of converting brat annotations"""

    @property
    def description(self) -> ProcessingDescription:
        return self._description

    def __init__(self, config=None):
        self._description = ProcessingDescription(
            name=self.__class__.__name__, config=config
        )

    def load(self, dir_path: str, text_extension: str) -> Collection:
        """
        Load the documents and the brat annotations into internal collection of
        documents

        Parameters
        ----------
        dir_path: str
            The path to the directory containing the text documents and the annotation
            files (.ann)
        text_extension: str
            The extension of the text document (e.g., .txt)

        Returns
        -------
        Collection
            The collection of documents (TextDocument)

        """
        documents = list()
        dir_path = pathlib.Path(dir_path)

        for text_path in dir_path.glob("*%s" % text_extension):
            ann_filename = text_path.stem + ".ann"
            ann_path = dir_path / ann_filename
            if ann_path.exists():
                documents.append(self._load_file(str(text_path), str(ann_path)))
        return Collection(documents)

    def _load_file(self, text_path: str, ann_path: str) -> TextDocument:
        """
        Internal method for loading an annotation file (.ann).

        Parameters
        ----------
        text_path: str
            The path to the text document file.
        ann_path: str
            The path to the brat annotation file.

        Returns
        -------
        TextDocument
            The internal Text Document

        """
        with open(text_path, encoding="utf-8") as text_file:
            text = text_file.read()
        filename = pathlib.Path(text_path).name
        metadata = {"name": filename}
        internal_doc = TextDocument(text=text, metadata=metadata)
        internal_doc.add_operation(self.description)
        brat_doc = brat_utils.parse_file(ann_path)
        # First convert entities, then relations, finally attributes
        # because new annotation id is needed
        brat_ann = dict()
        for brat_entity in brat_doc.entities.values():
            internal_entity = self._convert_brat_entity(brat_entity)
            internal_doc.add_annotation(internal_entity)
            brat_ann[brat_entity.id] = internal_entity.id
        for brat_relation in brat_doc.relations.values():
            internal_relation = self._convert_brat_relation(brat_relation, brat_ann)
            internal_doc.add_annotation(internal_relation)
            brat_ann[brat_relation.id] = internal_relation.id
        for brat_attribute in brat_doc.attributes.values():
            internal_attribute = self._convert_brat_attribute(brat_attribute, brat_ann)
            internal_doc.add_annotation(internal_attribute)
            brat_ann[brat_attribute.id] = internal_attribute.id
        return internal_doc

    def _convert_brat_entity(self, brat_entity: brat_utils.Entity) -> Entity:
        return Entity(
            origin=Origin(processing_id=self.description.id),
            label=brat_entity.type,
            spans=brat_entity.span,
            text=brat_entity.text,
            metadata={"brat_id": brat_entity.id},
        )

    def _convert_brat_relation(
        self, brat_relation: brat_utils.Relation, brat_ann: dict
    ) -> Relation:
        return Relation(
            origin=Origin(processing_id=self.description.id),
            label=brat_relation.type,
            source_id=brat_ann[brat_relation.subj],
            target_id=brat_ann[brat_relation.obj],
            metadata={"brat_id": brat_relation.id},
        )

    def _convert_brat_attribute(
        self, brat_attribute: brat_utils.Attribute, brat_ann: dict
    ) -> Attribute:
        return Attribute(
            origin=Origin(processing_id=self.description.id),
            label=brat_attribute.type,
            target_id=brat_ann[brat_attribute.target],
            value=brat_attribute.value,
            metadata={"brat_id": brat_attribute.id},
        )
