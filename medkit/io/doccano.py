
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union, ValuesView, Dict
import json
from smart_open import open

from medkit.core import (
    Attribute,
    InputConverter,
    OutputConverter,
    ProvTracer,
    generate_id,
    OperationDescription,
)
from medkit.core.text import (
    TextAnnotation,
    Entity,
    Relation,
    Segment,
    Span,
    TextDocument,
    span_utils,
)


JSONL_EXT =".jsonl"
TEXT_EXT = ".txt"


logger = logging.getLogger(__name__)


class doccanoJsonlConverter(InputConverter):
    """Class in charge of converting doccano annotations from jsonl"""

    def __init__(self, uid: Optional[str] = None):
        if uid is None:
            uid = generate_id()

        self.uid = uid
        self._prov_tracer: Optional[ProvTracer] = None

    @property
    def description(self) -> OperationDescription:
        return OperationDescription(
            uid=self.uid,
            name=self.__class__.__name__,
            class_name=self.__class__.__name__,
        )

    def set_prov_tracer(self, prov_tracer: ProvTracer):
        self._prov_tracer = prov_tracer

    def load(
        self,
        dir_path: Union[str, Path],
        jsonl_ext: str = JSONL_EXT,

    ) -> List[TextDocument]:
        """
        Create a list of TextDocuments from a folder containing jsonl files from doccano.

        Parameters
        ----------
        dir_path:
            The path to the directory containing the  jsonl files 


        Returns
        -------
        List[TextDocument]
            The list of TextDocuments
        """
        documents = list()
        dir_path = Path(dir_path)

        # find all base paths with at least a corresponding text or ann file
        base_paths = set()
        for ann_path in sorted(dir_path.glob("*" + jsonl_ext)):
            base_paths.add(dir_path / ann_path.stem)

        # load doc for each base_path
        for base_path in sorted(base_paths):

            ann_path = base_path.with_suffix(jsonl_ext)

            
            doc = self.load_doc(ann_path=ann_path)
            
            documents.append(doc)

        if not documents:
            logger.warning(f"Didn't load any document from dir {dir_path}")

        return documents

    def load_doc(
        self, ann_path: Union[str, Path], 
    ) -> TextDocument:
        """
        Create a TextDocument from a .jsonl file 

        Parameters
        ----------

        ann_path:
            The path to the jsonl doccano annotation file.

        Returns
        -------
        TextDocument
            The document containing the text and the annotations
        """

        ann_path = Path(ann_path)



        text,anns = self.load_annotations(ann_path)

        metadata = dict(path_to_ann=str(ann_path))

        doc = TextDocument(text=text, metadata=metadata)

        for ann in anns:
            doc.anns.add(ann)
            
        
        return doc

    def load_annotations(self, ann_file: Union[str, Path]) -> List[TextAnnotation]:
        """
        Load a .jsonl file and return the rax text and a list of
        :class:`~medkit.core.text.annotation.Annotation` objects.

        Parameters
        ----------
        ann_file:
            Path to the .jsonl file.
        """

       


        
        
        json_file= open(ann_file)
        doccano_doc=json.load(json_file)
        json_file.close()   
        anns_by_doccano_id = dict()


        # First convert entities, then relations, finally attributes
        # because new annotation identifier is needed
        text = doccano_doc["text"]
        for doccano_ent in doccano_doc["entities"]:
            entity = Entity(
           
                label=doccano_ent["label"],
                spans=[Span(doccano_ent["start_offset"],doccano_ent["end_offset"])],
                text=text[doccano_ent["start_offset"]:doccano_ent["end_offset"]],
                
            )
            anns_by_doccano_id[doccano_ent["id"]] = entity
            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    entity, self.description, source_data_items=[]
                )

        for doccano_relation in doccano_doc["relations"]:
            relation = Relation(
                label=doccano_relation["type"],
                source_id=anns_by_doccano_id[doccano_relation["from_id"]].uid,
                target_id=anns_by_doccano_id[doccano_relation["to_id"]].uid,
               
            )
            anns_by_doccano_id[relation.uid] = relation
            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    relation, self.description, source_data_items=[]
                )

       
        return text, list(anns_by_doccano_id.values())


