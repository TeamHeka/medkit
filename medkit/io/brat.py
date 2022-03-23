__all__ = ["BratInputConverter"]

from pathlib import Path
from typing import Optional, Union
import warnings

from smart_open import open

from medkit.core import (
    Collection,
    Attribute,
    Origin,
    InputConverter,
    OperationDescription,
)
from medkit.core.text import TextDocument, Entity, Relation
import medkit.io._brat_utils as brat_utils


class BratInputConverter(InputConverter):
    """Class in charge of converting brat annotations"""

    @property
    def description(self) -> OperationDescription:
        return self._description

    def __init__(self, id: Optional[str] = None):
        self._description = OperationDescription(
            id=id, name=self.__class__.__name__, config=None
        )

    def load(self, dir_path: Union[str, Path], text_extension: str) -> Collection:
        """
        Create a Collection of TextDocuments from a folder containting text files
        and associated brat annotations files (.ann).

        Parameters
        ----------
        dir_path:
            The path to the directory containing the text files and the annotation
            files (.ann)
        text_extension:
            The extension of the text file (e.g., .txt)

        Returns
        -------
        Collection
            The collection of TextDocuments
        """
        documents = list()
        dir_path = Path(dir_path)

        for text_path in dir_path.glob("*%s" % text_extension):
            ann_filename = text_path.stem + ".ann"
            ann_path = dir_path / ann_filename
            if ann_path.exists():
                documents.append(self._load_doc(text_path, ann_path))
        if not documents:
            warnings.warn(f"Didn't load any document from dir {dir_path}")
        return Collection(documents)

    def _load_doc(self, text_path: Path, ann_path: Path) -> TextDocument:
        """
        Create a TextDocument from text file and its associated annotation file (.ann)

        Parameters
        ----------
        text_path:
            The path to the text document file.
        ann_path:
            The path to the brat annotation file.

        Returns
        -------
        TextDocument
            The document containing the text and the annotations
        """
        with open(text_path, encoding="utf-8") as text_file:
            text = text_file.read()
        filename = text_path.name
        metadata = {"name": filename}
        doc = TextDocument(text=text, metadata=metadata)
        doc.add_operation(self.description)

        # First convert entities, then relations, finally attributes
        # because new annotation id is needed
        brat_doc = brat_utils.parse_file(ann_path)
        brat_ann = dict()

        for brat_entity in brat_doc.entities.values():
            entity = Entity(
                origin=Origin(operation_id=self.description.id),
                label=brat_entity.type,
                spans=brat_entity.span,
                text=brat_entity.text,
                metadata={"brat_id": brat_entity.id},
            )
            doc.add_annotation(entity)
            brat_ann[brat_entity.id] = entity

        for brat_relation in brat_doc.relations.values():
            relation = Relation(
                origin=Origin(operation_id=self.description.id),
                label=brat_relation.type,
                source_id=brat_ann[brat_relation.subj].id,
                target_id=brat_ann[brat_relation.obj].id,
                metadata={"brat_id": brat_relation.id},
            )
            doc.add_annotation(relation)
            brat_ann[brat_relation.id] = relation

        for brat_attribute in brat_doc.attributes.values():
            attribute = Attribute(
                origin=Origin(operation_id=self.description.id),
                label=brat_attribute.type,
                value=brat_attribute.value,
                metadata={"brat_id": brat_attribute.id},
            )
            brat_ann[brat_attribute.target].attrs.append(attribute)

        return doc
