__all__ = ["BratInputConverter", "BratOutputConverter"]
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union, ValuesView

from smart_open import open
import medkit.io._brat_utils as brat_utils
from medkit.core import Attribute, Collection, InputConverter, OutputConverter, Store
from medkit.core.text import Entity, Relation, Segment, Span, TextDocument


TEXT_EXT = ".txt"
ANN_EXT = ".ann"
ANN_CONF_FILE = "annotation.conf"


class BratInputConverter(InputConverter):
    """Class in charge of converting brat annotations"""

    def __init__(self, store: Optional[Store] = None, op_id: Optional[str] = None):
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)
        self.store: Optional[Store] = store

    def load(
        self,
        dir_path: Union[str, Path],
        ann_ext: str = ANN_EXT,
        text_ext: str = TEXT_EXT,
    ) -> Collection:
        """
        Create a Collection of TextDocuments from a folder containting text files
        and associated brat annotations files.

        Parameters
        ----------
        dir_path:
            The path to the directory containing the text files and the annotation
            files (.ann)
        ann_ext:
            The extension of the brat annotation file (e.g. .ann)
        text_ext:
            The extension of the text file (e.g. .txt)

        Returns
        -------
        Collection
            The collection of TextDocuments
        """
        documents = list()
        dir_path = Path(dir_path)

        # find all base paths with at least a corresponding text or ann file
        base_paths = set()
        for ann_path in sorted(dir_path.glob("*" + ann_ext)):
            base_paths.add(dir_path / ann_path.stem)
        for text_path in sorted(dir_path.glob("*" + text_ext)):
            base_paths.add(dir_path / text_path.stem)

        # load doc for each base_path
        for base_path in sorted(base_paths):
            text_path = base_path.with_suffix(text_ext)
            if not text_path.exists():
                text_path = None
            ann_path = base_path.with_suffix(ann_ext)
            if not ann_path.exists():
                ann_path = None
            doc = self._load_doc(ann_path=ann_path, text_path=text_path)
            documents.append(doc)

        if not documents:
            logging.warn(f"Didn't load any document from dir {dir_path}")

        return Collection(documents)

    def _load_doc(
        self, ann_path: Optional[Path] = None, text_path: Optional[Path] = None
    ) -> TextDocument:
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
        assert ann_path is not None or text_path is not None

        metadata = dict()
        if text_path is not None:
            metadata.update(path_to_text=text_path)
            with open(text_path, encoding="utf-8") as text_file:
                text = text_file.read()
        else:
            text = None

        if ann_path is not None:
            metadata.update(path_to_ann=ann_path)
            anns = self._load_anns(ann_path)
        else:
            anns = []

        doc = TextDocument(text=text, metadata=metadata, store=self.store)
        for ann in anns:
            doc.add_annotation(ann)

        return doc

    def _load_anns(
        self, ann_path: Path
    ) -> ValuesView[Union[Entity, Relation, Attribute]]:
        brat_doc = brat_utils.parse_file(ann_path)
        anns_by_brat_id = dict()

        # First convert entities, then relations, finally attributes
        # because new annotation id is needed
        for brat_entity in brat_doc.entities.values():
            entity = Entity(
                label=brat_entity.type,
                spans=[Span(*brat_span) for brat_span in brat_entity.span],
                text=brat_entity.text,
                metadata=dict(brat_id=brat_entity.id),
            )
            anns_by_brat_id[brat_entity.id] = entity
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    entity, self.description, source_data_items=[]
                )

        for brat_relation in brat_doc.relations.values():
            relation = Relation(
                label=brat_relation.type,
                source_id=anns_by_brat_id[brat_relation.subj].id,
                target_id=anns_by_brat_id[brat_relation.obj].id,
                metadata=dict(brat_id=brat_relation.id),
            )
            anns_by_brat_id[brat_relation.id] = relation
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    relation, self.description, source_data_items=[]
                )

        for brat_attribute in brat_doc.attributes.values():
            attribute = Attribute(
                label=brat_attribute.type,
                value=brat_attribute.value,
                metadata=dict(brat_id=brat_attribute.id),
            )
            anns_by_brat_id[brat_attribute.target].attrs.append(attribute)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    attribute, self.description, source_data_items=[]
                )

        return anns_by_brat_id.values()


class BratOutputConverter(OutputConverter):
    """Class in charge of converting a list/Collection of TextDocuments into a
    brat collection file"""

    def __init__(
        self,
        anns_labels: Optional[List[str]] = None,
        attrs: Optional[List[str]] = None,
        ignore_segments: bool = True,
        create_config: bool = True,
        op_id: Optional[str] = None,
    ):
        """
        Initialize the Brat output converter

        Parameters
        ----------
        anns_labels:
            Labels of medkit annotations to convert into Brat annotations.
            If `None` (default) all the annotations will converted
        attrs:
            Labels of medkit attributes to add in the annotations that will be included.
            If `None` (default) all medkit attributes found in the segments or relations
            will be converted to Brat attributes
        ignore_segments:
            If `True` medkit segments will be ignored. Only entities, attributes and relations
            will be converted to Brat annotations.  If `False` the medkit segments will be
            converted to Brat annotations as well.
        create_config:
            Whether to create a configuration file for the generated collection.
            This file defines the types of annotations generated, it is necessary for the correct
            visualization on Brat.
        op_id:
            Identifier of the converter
        """
        self.anns_labels = anns_labels
        self.attrs = attrs
        self.ignore_segments = ignore_segments
        self.create_config = create_config

    def convert(
        self,
        docs: Union[List[TextDocument], Collection],
        dir_path: Union[str, Path],
    ):
        """Convert a collection or list of TextDocuments into a brat collection
        For each collection or list of documents, a folder is created with
        the txt and ann files.

        Parameters
        ----------
        docs:
            List or Collection of medkit doc objects to convert
        dir_path:
            String or path object to save the generated files
        """

        if isinstance(docs, Collection):
            docs = [
                medkit_doc
                for medkit_doc in docs.documents
                if isinstance(medkit_doc, TextDocument)
            ]

        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        if self.create_config:
            ann_configuration = brat_utils.BratAnnConfiguration(
                entity_types=set(), relation_types=dict(), attribute_types=dict()
            )

        for medkit_doc in docs:
            doc_id = medkit_doc.id
            text = medkit_doc.text

            if text is not None:
                text_path = dir_path / f"{doc_id}{TEXT_EXT}"
                text_path.write_text(text, encoding="utf-8")

            segments, relations, attrs = self._get_anns_from_medkit_doc(medkit_doc)
            brat_anns, brat_str = brat_utils.convert_medkit_anns_to_brat(
                segments, relations, attrs
            )
            # save ann file
            ann_path = dir_path / f"{doc_id}{ANN_EXT}"
            ann_path.write_text(brat_str, encoding="utf-8")

            if self.create_config:
                # update annotation_conf file from each generated brat
                ann_configuration = brat_utils.get_configuration_from_anns(
                    brat_anns, config=ann_configuration
                )

        if self.create_config:
            # save configuration file
            conf_path = dir_path / ANN_CONF_FILE
            conf_path.write_text(str(ann_configuration), encoding="utf-8")

    def _get_anns_from_medkit_doc(
        self, medkit_doc: TextDocument
    ) -> Tuple[List[Segment], List[Relation], List[str]]:
        """Return selected annotations from a medkit document.
        `attrs` is a list of attribute labels to include for each
         entity/segment or relation found
        """
        annotations = medkit_doc.get_annotations()

        if self.anns_labels is not None:
            # filter annotations by label
            annotations = [ann for ann in annotations if ann.label in self.anns_labels]

        if self.anns_labels and annotations == []:
            # labels_anns were a list but none of the annotations
            # had a label of interest
            labels_str = ",".join(self.anns_labels)
            logging.warn(
                "No medkit annotations were included because none have"
                f" '{labels_str}' as label."
            )

        if self.attrs is None:
            # include all atributes
            attrs = set(attr.label for ann in annotations for attr in ann.attrs)
        else:
            attrs = self.attrs

        segments = []
        relations = []
        for ann in annotations:
            if isinstance(ann, Entity):
                segments.append(ann)
            elif isinstance(ann, Segment) and not self.ignore_segments:
                # In brat only entities exists, in some cases
                # a medkit document could include segments
                # that may be exported as entities
                segments.append(ann)
            elif isinstance(ann, Relation):
                relations.append(ann)

        return segments, relations, attrs
